# app/ — Django domain apps

All domain apps live under the `app/` package and are installed as `app.<name>`
(see `INSTALLED_APPS`). Each app owns its models, views, urls, admin and templates
(templates live centrally in `core/templates/<app>/`, not inside the app).

## Conventions for every app here
- Namespaced imports only: `from app.<app>.models import ...`.
- Views are `@login_required` and owner-scoped (`account__owner=request.user`).
- HTMX drives interactivity; views return partials from `core/templates/partials/`.
- Business logic that is more than a query goes in `services.py`, not the view.
- Money is USD with `$` (use the `money` / `pnl_class` template filters).
- Migrations are committed; run `make migrate` after model changes.

## The apps (each has its own AGENTS.md)
- [accounts/](accounts/AGENTS.md) — users, `TradingAccount`, auth, rate-limited login.
- [trades/](trades/AGENTS.md) — `Trade` (+ plans), journal blocks, images. The core model.
- [imports/](imports/AGENTS.md) — the Inbox: CSV/Myfxbook ingest, triage, plan linking.
- [journal/](journal/AGENTS.md) — 2-day trade reviews and weekly reviews.
- [analytics/](analytics/AGENTS.md) — calendar, charts, portal, notification context.
- [ai_review/](ai_review/AGENTS.md) — AI review hook (interface; backends in `api/ai`).

> `app/core/` is dead (contents moved to top-level `core/`). Don't add to it.
