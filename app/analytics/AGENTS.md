# app/analytics — calendar, charts, portal

Read-only aggregation and dashboards. Writes nothing to trades.

## Views / pages
- Portal (dashboard), P/L calendar, charts (pairs traded, pips, win rate).
- Calendar supports a granularity toggle (daily day-grid / monthly year-grid) to
  aggregate P/L; day cells are clickable to a day panel.
- Charts right-align per-pair stats; pair logos via the `pair_logo` filter.

## Files
- `services.py` — all aggregation (sums, win rate, per-pair, per-day). Views stay thin.
- `context_processors.py` — `pending_reviews`: exposes review/inbox counts and the
  nav badge (`inbox_count`), weekend/weekly-review flags. Registered in settings.

## Rules — P/L correctness
- Aggregate ONLY real trades: use `Trade.objects` (default manager already excludes
  plans) or filter `is_plan=False`. Never aggregate `all_objects`/`plans`.
- Money is USD `$` (`money` filter); colour via `pnl_class`.
- Everything owner-scoped.
