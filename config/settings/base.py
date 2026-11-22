"""
Shared Django settings for the Trading Journal.

This module holds everything common to every environment. The concrete
environment is chosen by ``config/settings/__init__.py`` via ``DJANGO_ENV``:

    DJANGO_ENV=dev   -> config.settings.dev   (default; SQLite + local media)
    DJANGO_ENV=prod  -> config.settings.prod  (Cloudflare + secure cookies)

See docs/deployment.md.
"""

import os
from pathlib import Path

# base.py lives at config/settings/base.py, so the repo root is three levels up.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


# --- Core ---------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-d@8(y2u4begn9e0-wr7$x)-9s$zr5t1vpr4wn0g",
)
# DEBUG is set per-environment in dev.py / prod.py.
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

# --- Applications -------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project-wide shared app
    "core",
    # Domain apps (under the app/ package)
    "app.accounts",
    "app.trades",
    "app.imports",
    "app.journal",
    "app.analytics",
    "app.ai_review",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_globals",
                "app.analytics.context_processors.pending_reviews",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database -----------------------------------------------------------
# A DATABASE_URL (Postgres) wins in any environment when present; otherwise
# each environment falls back to its own default (SQLite in dev). Defined in
# base so both dev and prod share one resolver.
from urllib.parse import parse_qs, unquote, urlparse  # noqa: E402


def database_from_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "localhost",
        "PORT": parsed.port or 5432,
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": os.environ.get(
                "POSTGRES_SSLMODE", query.get("sslmode", ["require"])[0]
            )
        },
    }


SQLITE_DATABASE = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": BASE_DIR / "db.sqlite3",
}

# --- Auth ---------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "portal"
LOGOUT_REDIRECT_URL = "login"

# --- i18n ---------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Manila"
USE_I18N = True
USE_TZ = True

# --- Static & media -----------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Plain static storage by default so dev/tests need no collectstatic.
    # prod.py swaps in WhiteNoise's hashed+compressed manifest storage.
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Backblaze B2 through its S3-compatible endpoint. Keep the bucket private;
# image fields receive short-lived signed URLs instead of public object URLs.
if b2_bucket := os.environ.get("B2_BUCKET_NAME"):
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": os.environ.get("B2_KEY_ID"),
            "secret_key": os.environ.get("B2_APPLICATION_KEY"),
            "bucket_name": b2_bucket,
            "endpoint_url": os.environ.get("B2_ENDPOINT_URL"),
            "region_name": os.environ.get("B2_REGION", "us-west-004"),
            "default_acl": None,
            "querystring_auth": True,
            "querystring_expire": int(os.environ.get("B2_SIGNED_URL_SECONDS", "3600")),
            "file_overwrite": False,
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Myfxbook transaction timestamps use the connected broker's local timezone.
MYFXBOOK_BROKER_TIMEZONE = os.environ.get("MYFXBOOK_BROKER_TIMEZONE", TIME_ZONE)
# Myfxbook has its own upstream delay and documents no general rate limit for
# personal account endpoints. Five minutes is a deliberately conservative,
# fresh polling interval; never configure below 60 seconds.
MYFXBOOK_SYNC_INTERVAL_SECONDS = max(
    int(os.environ.get("MYFXBOOK_SYNC_INTERVAL_SECONDS", "300")), 60
)

# --- Rate limiting (django-ratelimit) -----------------------------------
# Uses the default cache. Login view is decorated in accounts/views.py.
RATELIMIT_ENABLE = env_bool("RATELIMIT_ENABLE", True)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Environment-specific settings (DEBUG, DATABASES, security hardening) live in
# config/settings/dev.py and config/settings/prod.py, which import * from here.
