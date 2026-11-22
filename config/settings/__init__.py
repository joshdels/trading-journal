"""Environment dispatcher.

``DJANGO_SETTINGS_MODULE`` stays ``config.settings`` everywhere (manage.py,
wsgi, asgi, pytest). This module picks the concrete environment from
``DJANGO_ENV`` and re-exports it:

    DJANGO_ENV=dev   -> config.settings.dev   (default)
    DJANGO_ENV=prod  -> config.settings.prod
"""

import os

_ENV = os.environ.get("DJANGO_ENV", "dev").lower()

if _ENV in ("prod", "production"):
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403

SETTINGS_ENV = _ENV
