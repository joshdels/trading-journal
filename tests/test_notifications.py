from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from app.accounts.models import TradingAccount
from app.analytics.context_processors import pending_reviews
from app.trades.models import Trade

pytestmark = pytest.mark.django_db


def _open_trade(account):
    return Trade.objects.create(
        account=account,
        symbol="XAUUSD",
        direction=Trade.Direction.BUY,
        volume=Decimal("0.01"),
        entry_price=Decimal("3500"),
        entry_time=timezone.now(),
        status=Trade.Status.OPEN,
        source=Trade.Source.IMPORT,
        external_source="myfxbook",
        external_key=f"open:{account.pk}",
    )


def test_new_myfxbook_open_trade_appears_only_in_owner_inbox():
    user = get_user_model().objects.create_user("owner", password="x")
    other = get_user_model().objects.create_user("other", password="x")
    account = TradingAccount.objects.create(owner=user, name="IC Markets")
    other_account = TradingAccount.objects.create(owner=other, name="Other")
    trade = _open_trade(account)
    _open_trade(other_account)

    request = RequestFactory().get("/")
    request.user = user
    context = pending_reviews(request)

    assert context["open_trade_notifications_count"] == 1
    assert list(context["open_trade_notifications"]) == [trade]
    assert context["inbox_notification_count"] == 1


def test_trade_journal_is_private_to_account_owner(client):
    owner = get_user_model().objects.create_user("private-owner", password="x")
    other = get_user_model().objects.create_user("viewer", password="x")
    account = TradingAccount.objects.create(owner=owner, name="Private")
    trade = _open_trade(account)

    client.force_login(other)
    assert client.get(reverse("trade_detail", args=[trade.pk])).status_code == 404
