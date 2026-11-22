#!/bin/sh
set -eu

role="${1:-web}"

if [ "$role" = "web" ]; then
  if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    uv run python manage.py migrate --noinput
  fi
  exec uv run gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --access-logfile -
fi

if [ "$role" = "worker" ]; then
  exec uv run python manage.py sync_myfxbook --watch \
    --interval "${MYFXBOOK_SYNC_INTERVAL_SECONDS:-300}"
fi

exec "$@"
