# Architecture

## Layout

```
config/            Django project (settings, urls, wsgi)
app/               Domain apps (business logic + HTML/HTMX views)
  core/            Shared templates (base, partials), template tags, globals, helpers
  accounts/        TradingAccount + rate-limited auth
  trades/          Trade, Strategy, Tag, TradeImage — the core model
  journal/         TradeReview (2-day) + WeeklyReview
  imports/         ImportBatch + CSV import flow
  analytics/       Portal, calendar, charts (aggregation only, no models)
  ai_review/       App-facing AI review hook (delegates to api/)
api/               External integration boundary (talks OUT)
  mt5/             MT5 data: file parsers + live-sync client placeholder
  ai/              AI-review provider backends (none wired yet)
templates/         Page templates per app
static/css/        theme.css (MT5 dark palette)
media/             Uploaded trade screenshots (tracked with the app)
tests/             pytest suite
```

**Why the split:** `app/` holds everything that *is* the journal. `api/` holds
everything that talks to the outside world — MT5 and the AI provider. The
domain apps never import a vendor SDK directly; they go through `api/`, so
swapping a CSV import for live MT5 sync, or turning on AI review, touches only
`api/` and one thin service in `app/`.

## Data model

- **TradingAccount** — broker/account metadata. Never stores a password.
- **Trade** — symbol, direction, volume, entry/exit, SL/TP, P/L, commission,
  swap, strategy, tags, images. Computes `pips` and `net_profit`. On save,
  schedules `review_due_at = exit_time + 2 days`. Carries the unused
  `ai_review` hook fields.
- **TradeImage** — multiple screenshots per trade.
- **Strategy / Tag** — classification.
- **TradeReview** — one-to-one with Trade; the 2-day post-trade review.
- **WeeklyReview** — one per week, created during the weekend.
- **ImportBatch** — audit record per import; dedup is by `Trade.mt5_ticket`.

## Data flow

```
MT5 export (CSV)
   -> api.mt5.parsers.CsvParser.parse()      # normalise rows
   -> app.imports.services.import_rows()      # dedup by ticket, create Trades
   -> Trade rows
   -> app.analytics.services                  # calendar / pips / portfolio stats
   -> templates (HTMX partials for calendar nav, day drill-down, review form)
```

The 2-day review queue and weekend banner are driven by one query exposed to
every template via `app.analytics.context_processors.pending_reviews`. The
`check_reviews` management command prints the same data for cron.

## AI review (reserved)

`Trade.ai_review` / `ai_review_requested_at` exist now. `app.ai_review.services
.request_review(trade)` calls `api.ai.backends.get_backend()`, which currently
returns a `NullBackend`. To enable: implement a provider backend in `api/ai/`
and return it from `get_backend`. Nothing else changes.

## Extending to live MT5 sync

Implement `LiveMT5Adapter` in `api/mt5/client.py` with the same `parse()`
contract as the file parsers (MetaTrader5 package, Windows). `import_rows`
consumes its rows unchanged. See [mt5-import.md](mt5-import.md).
