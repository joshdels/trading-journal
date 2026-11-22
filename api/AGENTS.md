# api/ — external AI backends

Pluggable backends for the AI trade-review feature. This is the integration layer
the `app.ai_review` app calls into; it holds no Django models or views.

## What's here
- `ai/backends.py` — provider adapters behind a common interface so the review
  feature stays provider-agnostic (swap implementations without touching the app).

## Rules
- Keep this layer free of Django request/ORM concerns — take plain inputs, return
  plain results. `app/ai_review/services.py` orchestrates and persists.
- No provider is wired by default; the interface is reserved. Add a backend here,
  select it via settings/env — don't hardcode a vendor in the app.
- Never put secrets in code; read API keys from env.

> MT5/Myfxbook clients are NOT here — they live in `core/lib/mt5/`.
