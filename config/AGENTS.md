# config/ — project configuration

Django project config: the settings package, URL root, and WSGI/ASGI entrypoints.

## Settings package (`config/settings/`)
Split by environment, selected at import time by `DJANGO_ENV`:
- `base.py` — everything shared. Exposes helpers `env_bool`, `database_from_url`,
  and `SQLITE_DATABASE`. Default `staticfiles` storage is plain (dev/tests need
  no `collectstatic`). Environment-specific values (DEBUG, DATABASES, hardening)
  are NOT here.
- `dev.py` — `from .base import *`; DEBUG on; SQLite (an explicit `DATABASE_URL`
  still wins).
- `prod.py` — `from .base import *`; DEBUG off; Postgres via `DATABASE_URL`;
  Cloudflare proxy header + secure cookies + HSTS; WhiteNoise manifest static
  storage (requires `collectstatic` at deploy).
- `__init__.py` — dispatcher: imports `dev` (default) or `prod`
  (`DJANGO_ENV` in `prod`/`production`).

### Rules
- `DJANGO_SETTINGS_MODULE` stays `config.settings` — never point it at a submodule.
  manage.py / wsgi / asgi / pytest all rely on the dispatcher.
- Put a new env-dependent setting in dev AND prod (or derive from a `base` helper),
  not only in base. If it changes security posture, it belongs in prod.
- Secrets come from env vars only (`.env.example` documents them). Never commit `.env`.

## urls.py
Root URLconf. Apps are included under their prefixes (`trades/`, `inbox/`,
`journal/`, `health/`, plus `""` for accounts/analytics). Keep media served only
in dev.
