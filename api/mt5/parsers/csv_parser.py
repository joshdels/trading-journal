import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .base import MT5Parser

# Accepts an MT5-style deal export. Column names are matched case-insensitively
# against these aliases, so small broker variations still parse.
ALIASES = {
    "mt5_ticket": ["ticket", "position", "order", "deal"],
    "symbol": ["symbol", "item"],
    "direction": ["type", "direction"],
    "volume": ["volume", "lots", "size"],
    "entry_price": ["entry_price", "open_price", "price_open", "open"],
    "exit_price": ["exit_price", "close_price", "price_close", "close"],
    "sl": ["sl", "s/l", "stop_loss"],
    "tp": ["tp", "t/p", "take_profit"],
    "entry_time": ["entry_time", "open_time", "time_open", "open"],
    "exit_time": ["exit_time", "close_time", "time_close"],
    "profit": ["profit", "pnl"],
    "commission": ["commission", "comm"],
    "swap": ["swap"],
}

DATE_FORMATS = ["%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M"]


def _norm(name):
    """Lowercase a header and collapse spaces/slashes to underscores."""
    return (
        str(name).strip().lower()
        .replace("/", "_").replace(" ", "_").replace("__", "_")
    )


def _num(value, default=0):
    if value in (None, ""):
        return default
    try:
        return Decimal(str(value).replace(" ", "").replace(",", ""))
    except (InvalidOperation, ValueError):
        return default


def _dt(value):
    if not value:
        return None
    value = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class CsvParser(MT5Parser):
    kind = "csv"

    def parse(self, fileobj) -> list[dict]:
        text = fileobj.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        header_map = self._map_headers(reader.fieldnames or [])

        rows = []
        for raw in reader:
            lower = {_norm(k): v for k, v in raw.items() if k}
            row = {field: lower.get(col) for field, col in header_map.items()}
            direction = (row.get("direction") or "").strip().lower()
            if direction not in ("buy", "sell"):
                direction = "buy" if "buy" in direction else "sell"
            entry_dt = _dt(row.get("entry_time"))
            if not row.get("symbol") or entry_dt is None:
                continue
            rows.append({
                "mt5_ticket": int(_num(row.get("mt5_ticket"))) or None,
                "symbol": row["symbol"].strip().upper(),
                "direction": direction,
                "volume": _num(row.get("volume"), Decimal("0.01")),
                "entry_price": _num(row.get("entry_price")),
                "exit_price": _num(row.get("exit_price")) or None,
                "sl": _num(row.get("sl")) or None,
                "tp": _num(row.get("tp")) or None,
                "entry_time": self.to_aware(entry_dt),
                "exit_time": self.to_aware(_dt(row.get("exit_time"))) if _dt(row.get("exit_time")) else None,
                "profit": _num(row.get("profit")),
                "commission": _num(row.get("commission")),
                "swap": _num(row.get("swap")),
            })
        return rows

    @staticmethod
    def _map_headers(fieldnames):
        lower_fields = {_norm(f): _norm(f) for f in fieldnames}
        mapping = {}
        for field, aliases in ALIASES.items():
            for alias in aliases:
                if alias in lower_fields:
                    mapping[field] = alias
                    break
        return mapping
