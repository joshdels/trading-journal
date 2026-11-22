# docs/ — project documentation

Human-facing docs. Keep them in sync when you change the behaviour they describe.

## Files
- `architecture.md` — apps, data model, request flow, key decisions.
- `deployment.md` — prod setup: `DJANGO_ENV=prod`, Postgres, Cloudflare, B2,
  `collectstatic`, the background sync worker.
- `mt5-import.md` — how trade data gets in: CSV export + Myfxbook sync, the Inbox
  triage flow.

## Rules
- Prose for humans, not a changelog. Update the relevant file in the same change
  that alters the feature (new env var → `deployment.md`; import/Inbox change →
  `mt5-import.md`; model/flow change → `architecture.md`).
- Match the README's terms. No fiction or placeholder names.
