import io
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from app.accounts.models import TradingAccount
from app.trades.models import Trade, TradeImage

pytestmark = pytest.mark.django_db


def _png_bytes():
    # Smallest valid 1x1 PNG.
    import base64
    data = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9"
        "awAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(data)


@pytest.fixture
def logged_in(client):
    get_user_model().objects.create_user("joshua", password="pw12345")
    client.login(username="joshua", password="pw12345")
    return client


@pytest.fixture
def trade():
    user = get_user_model().objects.create_user("owner", password="x")
    acct = TradingAccount.objects.create(owner=user, name="A")
    now = timezone.now()
    return Trade.objects.create(
        account=acct, symbol="EURUSD", direction="buy", volume=Decimal("1.0"),
        entry_price=Decimal("1.08500"), exit_price=Decimal("1.08600"),
        entry_time=now - timedelta(hours=2), exit_time=now - timedelta(hours=1),
    )


@pytest.fixture(autouse=True)
def _tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def test_upload_multiple_images_at_stage(logged_in, trade):
    files = [
        SimpleUploadedFile(f"shot{i}.png", _png_bytes(), content_type="image/png")
        for i in range(3)
    ]
    resp = logged_in.post(
        f"/trades/{trade.pk}/images/",
        {"stage": "entry", "caption": "setup", "images": files},
    )
    assert resp.status_code == 200
    assert trade.images.filter(stage=TradeImage.Stage.ENTRY).count() == 3


def test_delete_image(logged_in, trade):
    img = TradeImage.objects.create(
        trade=trade, stage="exit",
        image=SimpleUploadedFile("x.png", _png_bytes(), content_type="image/png"),
    )
    resp = logged_in.post(f"/trades/{trade.pk}/images/{img.pk}/delete/")
    assert resp.status_code == 200
    assert trade.images.count() == 0
