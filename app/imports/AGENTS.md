# app/imports — the Inbox (ingest + triage)

Owns getting trades in and the Inbox where they land for review. Mounted at
`/inbox/` (the nav item is "Inbox"; the old "Import" label is gone).

## Flow
1. **Ingest** — CSV upload (`CsvParser`) or Myfxbook sync (`sync_myfxbook_connection`).
   Imported/synced trades are created `confirmed=False` and `source=IMPORT`.
2. **Triage** — `inbox` view lists unconfirmed trades. User confirms one or all
   (`inbox_confirm`), clearing them from the Inbox. Nav badge counts them.
3. **Plan linking** — the Inbox suggests a matching plan (same symbol+direction,
   entry within 3 days via `_suggest_plan`). `inbox_link` calls
   `link_plan_to_trade`, which moves the plan's journal/images onto the booked
   trade, carries strategy/tags/notes, confirms it, and archives the plan.

## Files
- `services.py` — `import_rows`, `sync_myfxbook_connection`, `link_plan_to_trade`.
  Keep ingest/merge logic here, not in views.
- `models.py` — `ImportBatch` (ingest audit), `MT5Connection` (Myfxbook session).
- `views.py` — `inbox`, `inbox_confirm`, `inbox_link`, `mt5_connection`, `mt5_sync`.
- management commands: `ingest`, `sync_myfxbook`, `test_myfxbook`.

## Rules
- The broker book is the source of truth for numbers. Only ever create unconfirmed
  trades on genuinely NEW rows (don't re-flag on sync updates — check `was_created`).
- Upload/sync are rate-limited (`@ratelimit`). Keep that.
