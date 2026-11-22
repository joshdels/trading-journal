# app/accounts — users & trading accounts

Authentication and the `TradingAccount` that every trade hangs off.

## Models
- `TradingAccount` — owner (FK to user), name, broker, login, server, currency,
  `is_default`. Ownership here is the anchor for all owner-scoping in the app
  (`Trade.account.owner`).

## Auth
- Simple username/password login; `LOGIN_URL=login`, redirects to `portal`.
- Login view is rate-limited (django-ratelimit, 5/min per IP). Keep that; prod
  additionally sits behind Cloudflare.

## Rules
- A user only ever sees their own accounts/trades — forms filter account
  querysets to `owner=request.user`, views filter `account__owner=request.user`.
- Don't broaden the login rate limit without reason.
