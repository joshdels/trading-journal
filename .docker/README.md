# Docker

The container supports two roles through the same image:

- `web` runs migrations and Gunicorn;
- `worker` runs the five-minute Myfxbook synchronization loop.

For local PostgreSQL development:

```bash
docker compose -f .docker/compose.yml up --build
```

Open `http://127.0.0.1:8000`. Set `MYFXBOOK_EMAIL` and
`MYFXBOOK_PASSWORD` in your shell or local `.env` before starting if the worker
should synchronize a real account.

For production, inject the Neon `DATABASE_URL`, B2 variables, Django secrets,
and `DJANGO_ENV=prod` through the hosting platform. Do not bake secrets into the
image. Render's native `render.yaml` remains the simplest supported deployment.
