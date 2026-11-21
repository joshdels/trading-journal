from datetime import datetime, timezone as dt_timezone

from django.utils import timezone

REQUIRED_KEYS = {
    "mt5_ticket", "symbol", "direction", "volume",
    "entry_price", "entry_time",
}


class MT5Parser:
    """Base contract for every MT5 history source."""

    kind = "csv"

    def parse(self, fileobj) -> list[dict]:
        raise NotImplementedError

    @staticmethod
    def to_aware(dt: datetime):
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, dt_timezone.utc)
        return dt

    @classmethod
    def validate(cls, row: dict) -> bool:
        return REQUIRED_KEYS.issubset(row.keys()) and row.get("symbol")
