# app/trades — trades, plans, journal

The heart of the app. Owns the `Trade` model and its journal.

## Models
- `Trade` — a position. Fields incl. execution (entry/exit/sl/tp, profit/commission/
  swap), `status`, `source`, external identity (`external_source`/`external_key`,
  unique per account), `confirmed` (Inbox triage), and the plan fields.
- `TradeImage` — stage-tagged screenshots (entry/exit/post).
- `JournalBlock` + `JournalBlockImage` — Wagtail-style timestamped log: per-stage
  blocks of note + multiple images, added/deleted via HTMX.
- `Strategy`, `Tag`.

## Plans (floating trades) — critical
A plan is a `Trade` with `is_plan=True`, `plan_status` (planned/realized/discarded),
and `realized_trade` FK. **Plans must never reach P/L math.**
- `Trade.objects` (default manager) EXCLUDES plans — analytics/calendar/charts use it.
- `Trade.all_objects` includes plans (used by `trade_detail`, admin).
- `Trade.plans` is plans-only.
- `Meta.base_manager_name = "all_objects"`.
When adding an aggregate query, confirm it goes through `Trade.objects` (or filters
`is_plan=False`). Linking a plan to a booked trade lives in `app/imports/services.py`.

## Views / forms
- Owner-scope everything. Journal + image add/delete return partials.
- `TradeForm` (full), `PlanForm` (intent-only subset), `JournalBlockForm`,
  `TradeImageUploadForm`, `TradeReviewForm`.
- Plan create sets `is_plan=True`, `confirmed=True` (plans don't sit in the Inbox).

## Gotchas
- `MultipleFileField`/`MultipleFileInput` (forms.py) back multi-image uploads.
- `pip_size()` handles JPY pairs and metals — don't assume 0.0001.
