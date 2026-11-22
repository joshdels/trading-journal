# tests/ — pytest suite

Centralised pytest-django tests (not per-app). Run with `make test` or `uv run pytest`.

## Files
- `test_models.py`, `test_views.py` — core model/view behaviour.
- `test_import.py`, `test_myfxbook_sync.py` — ingest + Myfxbook sync.
- `test_inbox.py` — Inbox triage (confirm one/all, listing).
- `test_plans.py` — plans excluded from P/L, suggestion + link/merge.
- `test_images.py`, `test_journal_blocks.py` — multi-image upload, journal blocks.
- `test_notifications.py` — review/weekly notification context.

## Conventions
- `pytestmark = pytest.mark.django_db` at module top for DB tests.
- A fixture that both logs in and owns data must use the SAME user. Owner-scoped
  views 404 otherwise — create the account under the logged-in user
  (`get_or_create(username="joshua")`), don't make a separate owner.
- Redirect media with an autouse fixture: `settings.MEDIA_ROOT = tmp_path`.
- Use the smallest valid 1×1 PNG for image uploads (see existing helpers).
- Hit URLs by path (`/inbox/`, `/trades/plans/new/`) consistent with `config/urls.py`.
- Keep assertions resilient to copy tweaks; prefer structural checks over exact
  marketing strings where practical.
