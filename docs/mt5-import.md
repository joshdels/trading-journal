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

## 2. Cloud sync through Myfxbook

Connect the MT5 investor account to Myfxbook, then sign in under **Import →
Connect Myfxbook**. Django stores the resulting IP-bound session, never the
Myfxbook password. Run `uv run python manage.py sync_myfxbook` every 15–30
minutes. The API returns only the latest 50 history records, so use a one-time
CSV import for older history; all imported rows remain permanently in Django.

## 3. Local Python terminal integration (Windows only)

The `MetaTrader5` Python package connects to a **locally running MT5 terminal**
on Windows and reads deals directly:

```python
import MetaTrader5 as mt5
mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER)
deals = mt5.history_deals_get(from_date, to_date)
```

This remains useful only when the Python process runs beside the MT5 terminal.

## Normalised row shape

```
mt5_ticket, symbol, direction (buy|sell), volume, entry_price, exit_price,
sl, tp, entry_time, exit_time, profit, commission, swap
```
# Myfxbook connection proof

The automatic connector is intentionally paused at the real-connection probe.
It does not write to the database. First connect the IC Markets MT5 account to
Myfxbook using its investor (read-only) password, then run:

```bash
export MYFXBOOK_EMAIL='your-myfxbook-email'
export MYFXBOOK_PASSWORD='your-myfxbook-password'
uv run python manage.py test_myfxbook
```

If Myfxbook contains several accounts and IC Markets cannot be identified from
the account name/server, select one explicitly using either its Myfxbook id or
MT5 account number:

```bash
uv run python manage.py test_myfxbook --account 53156944
```

The probe authenticates, calls `get-my-accounts`, `get-history`,
`get-open-trades`, and `get-open-orders`, prints only counts and observed field
names, and logs out in a `finally` block. It never prints credentials or the
session token. Myfxbook sessions are IP-bound and currently expire after one
month. Transaction timestamps are broker-local, and `get-history` returns at
most the latest 50 transactions. The observed real response must be reviewed
before the final PostgreSQL schema is designed.

## Automatic freshest-available synchronization

Myfxbook controls when MT5 changes reach its API, so the journal cannot promise
real-time updates. Once the real connection probe succeeds, run the sync worker
continuously. The default interval is five minutes:

```bash
export MYFXBOOK_EMAIL='your-myfxbook-email'
export MYFXBOOK_PASSWORD='your-myfxbook-password'
uv run python manage.py sync_myfxbook --watch
```

The environment credentials are used only to renew Myfxbook's IP-bound session
after it expires or becomes invalid. They are never written to the database or
logs. A custom interval can be configured, but values below 60 seconds are
rejected:

```bash
MYFXBOOK_SYNC_INTERVAL_SECONDS=300 uv run python manage.py sync_myfxbook --watch
```

For cron instead of a long-running worker, execute `sync_myfxbook` (without
`--watch`) every five minutes. Each cycle retrieves open trades, pending orders,
and the latest 50 history transactions. Open trades and closed history are
deduplicated into the journal; the pending-order count is reported for health
monitoring but pending orders are not journal trades and are not stored as
completed transactions.
