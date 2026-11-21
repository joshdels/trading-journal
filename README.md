# Trading Journal

A personal forex trading journal for MetaTrader 5 data. Django + HTMX + plain
CSS, styled in the MT5 dark terminal palette. SQLite and local media for
development. Managed with [uv](https://docs.astral.sh/uv/).

## Features

1. **Portal** — net P/L, win rate, trade counts, pending reviews, month calendar.
2. **P/L calendar** — profit/loss and trade count per day; click a day for its trades (HTMX).
3. **Trades** — entry/exit, SL/TP, pips, strategy, tags, notes, and multiple screenshots per trade.
4. **2-day review queue** — each closed trade opens a post-trade review 2 days after exit; overdue ones surface on the portal with a badge.
5. **Weekly review** — a weekend banner nudges you; record a summary per week.
6. **Pips-by-pair chart** — net pips per symbol as inline bars (no JS charting lib).
7. **MT5 import** — upload a CSV deal export; re-imports are idempotent (dedup by ticket).

The AI-review hook is wired into the data model (`Trade.ai_review`) and a
pluggable backend in `api/ai/`, but no provider is connected yet.

## Structure

```
config/   Django project settings/urls
app/      Domain apps: core, accounts, trades, journal, imports, analytics, ai_review
api/      External integrations: api/mt5 (parsers + live client), api/ai (review backends)
templates/  Page templates (shared base + partials live in app/core/templates)
static/   theme.css (MT5 palette)
docs/     architecture, mt5-import, deployment
tests/    pytest suite
```

See [docs/architecture.md](docs/architecture.md) for the why.

## Quick start

```bash
uv sync                               # create the env from the lockfile
uv run python manage.py migrate
uv run python manage.py seed_demo     # realistic demo data (user: joshua / changeme123)
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in. **Change the demo password before real
use:** `uv run python manage.py changepassword joshua`.

Wipe demo data: `uv run python manage.py seed_demo --wipe`.

### Make shortcuts

```bash
make install   # uv sync
make migrate   # apply migrations
make seed      # seed demo data
make run       # dev server
make test      # pytest
```

## Commands

- `seed_demo [--trades N] [--wipe]` — seed/remove realistic demo data.
- `check_reviews` — print trades due for review and the weekend-review status (cron-friendly).

## Tests

```bash
uv run pytest
```

## Docs

- [docs/architecture.md](docs/architecture.md) — apps, data model, data flow.
- [docs/mt5-import.md](docs/mt5-import.md) — exporting/importing MT5 history; live-sync path.
- [docs/deployment.md](docs/deployment.md) — production, Cloudflare, rate limiting.

## Stack

Python 3.15 · Django 6.1 · HTMX 2 · Phosphor Icons · SQLite · Pillow ·
django-ratelimit · pytest. Timezone: `Asia/Manila`.
