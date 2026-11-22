from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from app.accounts.models import TradingAccount
from app.imports.services import import_rows
from app.trades.models import Trade

pytestmark = pytest.mark.django_db


@pytest.fixture
def account():
    user, _ = get_user_model().objects.get_or_create(username="joshua")
    return TradingAccount.objects.create(owner=user, name="A")


@pytest.fixture
def logged_in(client):
    get_user_model().objects.get_or_create(username="joshua")
    user = get_user_model().objects.get(username="joshua")
    user.set_password("pw12345")
    user.save()
    client.login(username="joshua", password="pw12345")
    return client


def _row(ticket):
    now = timezone.now()
    return {
        "mt5_ticket": ticket, "symbol": "EURUSD", "direction": "buy",
        "volume": Decimal("1.0"), "entry_price": Decimal("1.0850"),
        "exit_price": Decimal("1.0860"), "entry_time": now - timedelta(hours=2),
        "exit_time": now - timedelta(hours=1), "profit": Decimal("10"),
    }


def test_imported_trades_land_unconfirmed(account):
    import_rows(account=account, rows=[_row(1), _row(2)], kind="csv")
    assert Trade.objects.filter(confirmed=False).count() == 2


def test_inbox_lists_pending(logged_in, account):
    import_rows(account=account, rows=[_row(1)], kind="csv")
    resp = logged_in.get("/inbox/")
    assert resp.status_code == 200
    assert b"Synced trades needing a journal report" in resp.content
    assert b"EURUSD" in resp.content


def test_confirm_single_clears_it(logged_in, account):
    import_rows(account=account, rows=[_row(1), _row(2)], kind="csv")
    t = Trade.objects.first()
    resp = logged_in.post("/inbox/confirm/", {"trade": t.pk})
    assert resp.status_code == 302
    t.refresh_from_db()
    assert t.confirmed is True
    assert Trade.objects.filter(confirmed=False).count() == 1


def test_confirm_all(logged_in, account):
    import_rows(account=account, rows=[_row(1), _row(2)], kind="csv")
    logged_in.post("/inbox/confirm/")
    assert Trade.objects.filter(confirmed=False).count() == 0
