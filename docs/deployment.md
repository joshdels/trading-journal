# Deployment notes

This is a personal, single-user app. Development uses SQLite and local media.
These notes cover taking the same code to production behind Cloudflare.

## Environment variables

Settings read these in production (see `config/settings.py`):

| Variable | Purpose |
|----------|---------|
| `DJANGO_DEBUG` | `false` in prod (turns on the hardening block). |
| `DJANGO_SECRET_KEY` | Required. Generate a fresh random key. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated `https://` origins. |
| `RATELIMIT_ENABLE` | Keep `true`. |
| `SECURE_SSL_REDIRECT` | `true` to force HTTPS. |

Copy `.env.example` to `.env` and fill it in.

## Cloudflare (spam / abuse shield)

Cloudflare sits in front of the app in production and is the first line against
bots and spam:

- **TLS** terminates at Cloudflare. Django trusts `X-Forwarded-Proto` via
  `SECURE_PROXY_SSL_HEADER` (set automatically when `DEBUG=false`) so it knows
  requests are HTTPS.
- **Bot / rate protection**: enable a WAF rate-limiting rule on `/login/` and
  Bot Fight Mode in the Cloudflare dashboard. This complements the app-level
  throttle below.
- **Real client IP**: Cloudflare sends the visitor IP in `CF-Connecting-IP`.
  The app-level rate limit keys on IP, so in production put a small middleware
  (or `django-ipware`) in front to set `REMOTE_ADDR` from `CF-Connecting-IP`,
  and restrict inbound traffic to Cloudflare's IP ranges at the firewall so the
  header can't be spoofed.

## App-level rate limiting (django-ratelimit)

Already wired, independent of Cloudflare:

- Login: **5 POST/min per IP** (`app/accounts/views.py`).
- Import upload: **10 POST/min per user** (`app/imports/views.py`).

The default cache is in-memory (`LocMemCache`) — fine for one process. For
multiple workers, switch `CACHES` to Redis/Memcached so limits are shared.

## Static & media

```bash
uv run python manage.py collectstatic
```

Serve `STATIC_ROOT` via the web server / Cloudflare, and `MEDIA_ROOT`
(trade screenshots) from persistent storage. For a bigger setup, move media to
object storage.

## Database

SQLite is fine for one user. To move to Postgres, change `DATABASES` and
re-run migrations — no model changes needed.
