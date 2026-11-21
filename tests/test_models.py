from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from app.accounts.models import TradingAccount
from app.trades.models import Trade, pip_size

pytestmark = pytest.mark.django_db


@pytest.fixture
def account():
    user = get_user_model().objects.create_user("t", password="x")
    return TradingAccount.objects.create(owner=user, name="A")


def make_trade(account, **kw):
    now = timezone.now()
    defaults = dict(
        account=account, symbol="EURUSD", direction="buy", volume=Decimal("1.00"),
        entry_price=Decimal("1.08500"), exit_price=Decimal("1.08600"),
        entry_time=now - timedelta(hours=2), exit_time=now - timedelta(hours=1),
        profit=Decimal("10.00"), status=Trade.Status.CLOSED,
    )
    defaults.update(kw)
    return Trade.objects.create(**defaults)


def test_pip_size():
    assert pip_size("EURUSD") == 0.0001
    assert pip_size("USDJPY") == 0.01
    assert pip_size("XAUUSD") == 0.1


def test_pips_buy(account):
    t = make_trade(account)  # +10 points on EURUSD = +10 pips
    assert t.pips == 10.0


def test_pips_sell_inverts(account):
    t = make_trade(account, direction="sell")  # price rose → sell loses pips
    assert t.pips == -10.0


def test_review_due_scheduled_from_exit(account):
    t = make_trade(account)
    assert t.review_due_at == t.exit_time + timedelta(days=2)


def test_review_overdue_flag(account):
    past = timezone.now() - timedelta(days=5)
    t = make_trade(account, exit_time=past)
    assert t.review_overdue is True
    t.review_completed = True
    assert t.review_overdue is False


def test_net_profit_includes_costs(account):
    t = make_trade(account, profit=Decimal("10"), commission=Decimal("-0.70"), swap=Decimal("-0.30"))
    assert t.net_profit == pytest.approx(9.0)
