"""Development settings: SQLite + local media, DEBUG on, no HTTPS assumptions.

This is the default environment (``DJANGO_ENV`` unset). An explicit
``DATABASE_URL`` still wins so you can point dev at a real Postgres if needed.
"""

import os

from .base import *  # noqa: F401,F403
from .base import SQLITE_DATABASE, database_from_url, env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)

DATABASES = {
    "default": database_from_url(os.environ["DATABASE_URL"])
    if os.environ.get("DATABASE_URL")
    else SQLITE_DATABASE
}

# Rate limiting stays on by default but is trivial to disable while hacking.
RATELIMIT_ENABLE = env_bool("RATELIMIT_ENABLE", True)
