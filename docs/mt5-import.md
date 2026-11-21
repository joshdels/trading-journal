# Getting MT5 data in

There is **no official web API** that takes an MT5 login/password and returns
your trade history. The realistic paths, in order of how this project uses them:

## 1. CSV import (works everywhere, used now)

1. In MetaTrader 5: **Toolbox → History** tab.
2. Right-click → **Report → CSV** (or select a date range first).
3. In the journal: **Import** → pick the account → upload the CSV.

Re-importing is safe: rows are deduplicated by the MT5 ticket, so only new
trades are created. Every import is logged as an `ImportBatch`.

The parser (`api/mt5/parsers/csv_parser.py`) matches columns case-insensitively
and tolerates spaces/slashes in headers (`Open Time`, `S/L`), plus common
broker aliases (`Open Price`/`Price Open`, `Lots`/`Volume`, etc.).

## 2. Live sync (later, Windows only)

The `MetaTrader5` Python package connects to a **locally running MT5 terminal**
on Windows and reads deals directly:

```python
import MetaTrader5 as mt5
mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER)
deals = mt5.history_deals_get(from_date, to_date)
```

Implement this as `LiveMT5Adapter` in `api/mt5/client.py`, returning the same
normalised row dicts the file parsers produce (keys listed in
`api/mt5/parsers/__init__.py`). Because `app.imports.services.import_rows`
consumes that shape, nothing downstream changes.

Credentials are supplied at sync time and **never stored** by the app.

## Normalised row shape

```
mt5_ticket, symbol, direction (buy|sell), volume, entry_price, exit_price,
sl, tp, entry_time, exit_time, profit, commission, swap
```
