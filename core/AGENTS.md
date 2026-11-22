# core/ — shared, cross-app code

The `core` app holds everything shared across domain apps. No business/domain
models live here.

## What's here
- `templates/` — ALL templates for every app, organised by app
  (`templates/trades/`, `templates/imports/`, `templates/analytics/`, …) plus
  `templates/partials/` for HTMX fragments and `base.html` (nav, theme toggle).
- `static/css/theme.css` — the single global stylesheet (MT5 dark palette via CSS
  vars `--accent`, `--green`/`--red`, `--border`, `--muted`). Scoped `<style>` in
  a partial is fine to avoid touching this during parallel work.
- `templatetags/journal_extras.py` — filters: `money` (USD `$`), `pnl_class`,
  `pips`, `pair_logo`. Load with `{% load journal_extras %}`.
- `context_processors.py` — `site_globals` (brand/nav globals).
- `views.py` — tiny shared views (e.g. `health`).
- `constants.py`, `utils.py` — shared helpers.
- `lib/` — external service clients. `lib/mt5/` has `myfxbook.py` (and `client.py`)
  for the Myfxbook/MT5 sync. Keep HTTP/parsing concerns here, out of views.

## Rules
- Template lookups are by `"<app>/<name>.html"` (APP_DIRS off; central dirs).
- Theme colours come from CSS vars — don't hardcode hex in templates.
- `lib/` clients raise their own typed errors (e.g. `MyfxbookError`); callers in
  `app/imports/services.py` translate them to user messages.
