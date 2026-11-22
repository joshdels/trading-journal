# app/ai_review — AI trade review (hook)

The AI review feature. Interface is reserved; no provider is wired by default.

## Shape
- `models.py` — stores review requests/results (the `Trade` also has
  `ai_review` / `ai_review_requested_at` fields as the entry point).
- `services.py` — orchestrates: gather trade context → call a backend → persist.
- Backends live in `api/ai/backends.py` (provider-agnostic). This app must not
  hardcode a vendor or SDK.

## Rules
- Keep ORM/request concerns here; keep provider/HTTP concerns in `api/ai`.
- Selecting/enabling a backend is config-driven (settings/env), never inline.
- No secrets in code.
