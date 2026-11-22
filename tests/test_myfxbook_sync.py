from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from app.accounts.models import TradingAccount
from app.imports.models import MT5Connection
from app.imports.services import sync_myfxbook_connection
from app.trades.models import Trade

pytestmark = pytest.mark.django_db


@pytest.fixture
def connection():
    user = get_user_model().objects.create_user("sync-user", password="x")
    account = TradingAccount.objects.create(owner=user, name="IC Markets", login="53156944")
    return MT5Connection.objects.create(
        account=account,
        state="connected",
        myfxbook_account_id="12345",
        myfxbook_session="secret-session",
        session_expires_at=timezone.now() + timedelta(days=5),
    )


def test_sync_imports_open_and_closed_without_duplicates(connection, monkeypatch):
    open_trade = {
        "openTime": "11/22/2026 10:00", "symbol": "XAUUSD", "action": "Sell",
        "sizing": {"type": "lots", "value": "0.01"}, "openPrice": 3570.13,
        "profit": -2.5, "swap": 0, "sl": 3593.60, "tp": 3500,
    }
    closed_trade = {
        **open_trade, "closeTime": "11/22/2026 11:00", "closePrice": 3560,
        "profit": 10.13, "commission": -0.07, "interest": 0,
    }
    responses = iter((
        ([open_trade], [{"symbol": "EURGBP"}], []),
        ([], [], [closed_trade]),
        ([], [], [closed_trade]),
    ))
    monkeypatch.setattr("app.imports.services._myfxbook_payload", lambda unused: next(responses))

    first = sync_myfxbook_connection(connection)
    second = sync_myfxbook_connection(connection)
    third = sync_myfxbook_connection(connection)

    assert first["pending_orders"] == 1
    assert second["created"] == 0
    assert third["created"] == 0
    assert Trade.objects.filter(account=connection.account).count() == 1
    trade = Trade.objects.get(account=connection.account)
    assert trade.status == Trade.Status.CLOSED
    assert trade.symbol == "XAUUSD"


def test_expired_session_is_not_skipped_by_sync_command(connection, monkeypatch):
    connection.session_expires_at = timezone.now() - timedelta(minutes=1)
    connection.save(update_fields=["session_expires_at"])
    called = []
    monkeypatch.setattr(
        "app.imports.management.commands.sync_myfxbook.sync_myfxbook_connection",
        lambda item: called.append(item.pk) or {
            "positions": 0, "pending_orders": 0, "history": 0, "created": 0
        },
    )
    from django.core.management import call_command

    call_command("sync_myfxbook")
    assert called == [connection.pk]
