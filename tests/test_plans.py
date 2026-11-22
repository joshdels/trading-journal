from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from app.accounts.models import TradingAccount
from app.imports.services import link_plan_to_trade
from app.trades.models import JournalBlock, Strategy, Trade

pytestmark = pytest.mark.django_db


@pytest.fixture
def account():
    user, _ = get_user_model().objects.get_or_create(username="joshua")
    return TradingAccount.objects.create(owner=user, name="A")


@pytest.fixture
def logged_in(client):
    user, _ = get_user_model().objects.get_or_create(username="joshua")
    user.set_password("pw12345")
    user.save()
    client.login(username="joshua", password="pw12345")
    return client


def _plan(account, **kw):
    now = timezone.now()
    defaults = dict(
        account=account, symbol="EURUSD", direction="buy", volume=Decimal("1.0"),
        entry_price=Decimal("1.0850"), entry_time=now, is_plan=True,
        plan_status=Trade.PlanStatus.PLANNED, status=Trade.Status.OPEN,
    )
    defaults.update(kw)
    return Trade.all_objects.create(**defaults)


def _trade(account, **kw):
    now = timezone.now()
    defaults = dict(
        account=account, symbol="EURUSD", direction="buy", volume=Decimal("1.0"),
        entry_price=Decimal("1.0853"), exit_price=Decimal("1.0870"),
        entry_time=now, exit_time=now + timedelta(hours=1),
        profit=Decimal("17"), source=Trade.Source.IMPORT, confirmed=False,
    )
    defaults.update(kw)
    return Trade.objects.create(**defaults)


def test_plans_excluded_from_default_manager(account):
    _plan(account)
    _trade(account)
    assert Trade.objects.count() == 1          # real trade only
    assert Trade.plans.count() == 1            # plan only
    assert Trade.all_objects.count() == 2


def test_link_merges_journal_and_archives_plan(account):
    strat = Strategy.objects.create(name="Breakout")
    plan = _plan(account, strategy=strat, notes="London range break")
    JournalBlock.objects.create(trade=plan, stage="entry", note="setup forming")
    trade = _trade(account)

    link_plan_to_trade(plan, trade)
    trade.refresh_from_db()
    plan.refresh_from_db()

    # Journal moved to the real trade.
    assert trade.journal_blocks.count() == 1
    assert plan.journal_blocks.count() == 0
    # Metadata carried over, trade confirmed.
    assert trade.strategy_id == strat.id
    assert "London range break" in trade.notes
    assert trade.confirmed is True
    # Plan archived and linked.
    assert plan.plan_status == Trade.PlanStatus.REALIZED
    assert plan.realized_trade_id == trade.id


def test_inbox_link_endpoint_suggests_and_links(logged_in, account):
    plan = _plan(account)
    trade = _trade(account)
    # Suggestion surfaces on the inbox page.
    page = logged_in.get("/inbox/")
    assert b"Matches your plan" in page.content
    # Linking via the endpoint.
    resp = logged_in.post("/inbox/link/", {"trade": trade.pk, "plan": plan.pk})
    assert resp.status_code == 302
    trade.refresh_from_db()
    plan.refresh_from_db()
    assert trade.confirmed is True
    assert plan.plan_status == Trade.PlanStatus.REALIZED


def test_plan_create_view(logged_in, account):
    resp = logged_in.post("/trades/plans/new/", {
        "account": account.pk, "symbol": "GBPUSD", "direction": "sell",
        "volume": "0.5", "entry_price": "1.2700",
        "entry_time": timezone.now().strftime("%Y-%m-%dT%H:%M"),
    })
    assert resp.status_code == 302
    plan = Trade.plans.get(symbol="GBPUSD")
    assert plan.is_plan is True
    assert Trade.objects.filter(symbol="GBPUSD").count() == 0  # not in real trades
