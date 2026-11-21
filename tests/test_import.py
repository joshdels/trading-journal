import io

import pytest
from django.contrib.auth import get_user_model

from app.accounts.models import TradingAccount
from app.imports.services import import_rows
from app.trades.models import Trade
from api.mt5.parsers import CsvParser

pytestmark = pytest.mark.django_db

CSV = """Ticket,Symbol,Type,Volume,Open Price,Close Price,Open Time,Close Time,Profit,Commission,Swap
101,EURUSD,buy,1.00,1.08500,1.08650,2026.11.01 09:00:00,2026.11.01 12:00:00,15.00,-0.70,0
102,USDJPY,sell,0.50,150.500,150.200,2026.11.02 08:00:00,2026.11.02 10:00:00,10.00,-0.35,0
"""


@pytest.fixture
def account():
    user = get_user_model().objects.create_user("t", password="x")
    return TradingAccount.objects.create(owner=user, name="A")


def test_csv_parses_rows():
    rows = CsvParser().parse(io.BytesIO(CSV.encode()))
    assert len(rows) == 2
    assert rows[0]["symbol"] == "EURUSD"
    assert rows[0]["mt5_ticket"] == 101
    assert rows[1]["direction"] == "sell"


def test_import_is_idempotent(account):
    rows = CsvParser().parse(io.BytesIO(CSV.encode()))
    b1 = import_rows(account, rows, kind="csv")
    assert b1.rows_created == 2
    # Re-import the same file: nothing new created.
    rows2 = CsvParser().parse(io.BytesIO(CSV.encode()))
    b2 = import_rows(account, rows2, kind="csv")
    assert b2.rows_created == 0
    assert b2.rows_skipped == 2
    assert Trade.objects.count() == 2
