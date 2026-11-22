"""Production settings: Postgres + Cloudflare + secure cookies, DEBUG off.

Cloudflare sits in front: it terminates TLS and shields the origin from spam
bots. We trust its forwarded-proto header so Django knows requests are HTTPS,
and read the real visitor IP from CF-Connecting-IP for rate-limit keys.
See docs/deployment.md.
"""

import os

from .base import *  # noqa: F401,F403
from .base import STORAGES, SQLITE_DATABASE, database_from_url, env_bool

DEBUG = env_bool("DJANGO_DEBUG", False)

# Hashed + compressed static files, served by WhiteNoise. Requires
# `collectstatic` at deploy time (see docs/deployment.md).
STORAGES["staticfiles"] = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
}

# Postgres in prod; fall back to SQLITE only if DATABASE_URL is truly unset
# (e.g. a smoke test), never silently in a real deployment.
DATABASES = {
    "default": database_from_url(os.environ["DATABASE_URL"])
    if os.environ.get("DATABASE_URL")
    else SQLITE_DATABASE
}

RATELIMIT_ENABLE = env_bool("RATELIMIT_ENABLE", True)

# --- Security hardening -------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "2592000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
