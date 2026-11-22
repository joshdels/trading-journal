import base64
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from app.accounts.models import TradingAccount
from app.trades.models import JournalBlock, Trade

pytestmark = pytest.mark.django_db

_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.fixture(autouse=True)
def _tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def logged_in(client):
    get_user_model().objects.create_user("joshua", password="pw12345")
    client.login(username="joshua", password="pw12345")
    return client


@pytest.fixture
def trade():
    user, _ = get_user_model().objects.get_or_create(username="joshua")
    acct = TradingAccount.objects.create(owner=user, name="A")
    now = timezone.now()
    return Trade.objects.create(
        account=acct, symbol="EURUSD", direction="buy", volume=Decimal("1.0"),
        entry_price=Decimal("1.08500"), exit_price=Decimal("1.08600"),
        entry_time=now - timedelta(hours=2), exit_time=now - timedelta(hours=1),
    )


def test_add_block_with_note_and_images(logged_in, trade):
    files = [SimpleUploadedFile(f"s{i}.png", _PNG, content_type="image/png") for i in range(2)]
    resp = logged_in.post(
        f"/trades/{trade.pk}/journal/add/",
        {"stage": "entry", "note": "broke the London range", "images": files},
    )
    assert resp.status_code == 200
    block = trade.journal_blocks.get()
    assert block.stage == "entry"
    assert block.note == "broke the London range"
    assert block.images.count() == 2


def test_block_requires_note_or_image(logged_in, trade):
    logged_in.post(f"/trades/{trade.pk}/journal/add/", {"stage": "entry", "note": ""})
    assert trade.journal_blocks.count() == 0


def test_delete_block(logged_in, trade):
    b = JournalBlock.objects.create(trade=trade, stage="post", note="review done")
    resp = logged_in.post(f"/trades/{trade.pk}/journal/{b.pk}/delete/")
    assert resp.status_code == 200
    assert trade.journal_blocks.count() == 0
