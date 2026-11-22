# Trading Journal — agent guide

Personal forex trading journal for MetaTrader 5 data. Django + HTMX + plain CSS,
SQLite + local media in dev, Postgres + Backblaze B2 in prod. MT5-terminal dark
theme (green profit / red loss). Timezone **Asia/Manila**. P/L shown as USD `$`.

This file is intentionally short. Each major directory has its own `AGENTS.md`
with the rules that apply there — read the nested one before working in a tree.

## Commands (use `make`; uv underneath, never pip/requirements.txt)
- `make run` — dev server
- `make migrate` — makemigrations + migrate
- `make test` — pytest suite
- `make seed` / `make install` — demo data / deps

Run anything ad hoc through uv: `uv run python manage.py <cmd>`, `uv run pytest`.

## Settings: dev vs prod
`config/settings/` is a package picked by `DJANGO_ENV` (default `dev`).
`DJANGO_SETTINGS_MODULE` stays `config.settings` everywhere. See
[config/AGENTS.md](config/AGENTS.md).

## Layout (→ nested guides)
- `app/` — Django domain apps. See [app/AGENTS.md](app/AGENTS.md).
- `core/` — shared templates, static, template tags, context processors, and
  `core/lib/` external clients (Myfxbook/MT5). See [core/AGENTS.md](core/AGENTS.md).
- `config/` — settings package, urls, wsgi/asgi. See [config/AGENTS.md](config/AGENTS.md).
- `api/` — AI backends for the review feature. See [api/AGENTS.md](api/AGENTS.md).
- `docs/` — architecture, deployment, MT5 import notes. See [docs/AGENTS.md](docs/AGENTS.md).
- `tests/` — pytest suite (top-level, not per-app). See [tests/AGENTS.md](tests/AGENTS.md).

## Global conventions
- **Imports are namespaced**: `from app.trades.models import ...`, never
  `from trades.models import ...`.
- **Owner-scope every lookup**: user-facing views filter by
  `account__owner=request.user` (avoids IDOR). `get_object_or_404` included.
- **Plans never touch P/L**: the default `Trade.objects` manager excludes planned
  (floating) trades. Use `Trade.all_objects` / `Trade.plans` deliberately.
- **No fiction**: realistic FX pairs and demo data only; Phosphor icons for UI.
- **Latest** Python / Django / libs (currently Py 3.15, Django 6.x).
- Keep CSS in `core/static/css/theme.css` or scoped `<style>` in partials.
