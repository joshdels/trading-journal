# Deploy on Render with Neon and Backblaze B2

Production is split into four responsibilities:

```text
Render web service     Django, HTMX, Gunicorn, WhiteNoise static files
Render worker          Myfxbook polling every five minutes
Neon                   PostgreSQL journal data
Backblaze B2           Private screenshots and journal images
```

## 1. Create the Neon database

Create a Neon project and copy its pooled PostgreSQL connection string. It
should use the `-pooler` hostname and include `sslmode=require`:

```text
postgresql://USER:PASSWORD@ep-example-pooler.REGION.aws.neon.tech/neondb?sslmode=require
```

Set this as Render's `DATABASE_URL`. Do not commit it.

## 2. Create private B2 image storage

1. Create a private Backblaze B2 bucket, such as `trading-journal-media`.
2. Create a bucket-restricted application key; do not use the master key.
3. Copy the bucket's S3 endpoint and region from Backblaze.
4. Configure these Render variables:

| Variable | Example / purpose |
| --- | --- |
| `B2_BUCKET_NAME` | `trading-journal-media` |
| `B2_KEY_ID` | B2 Key ID / S3 access-key equivalent |
| `B2_APPLICATION_KEY` | B2 application key / S3 secret-key equivalent |
| `B2_ENDPOINT_URL` | `https://s3.us-west-004.backblazeb2.com` |
| `B2_REGION` | `us-west-004` |
| `B2_SIGNED_URL_SECONDS` | `3600` |

Django uses B2 only when `B2_BUCKET_NAME` is present. Local development keeps
using `media/`. The bucket remains private and image URLs expire automatically.

## 3. Deploy the Render Blueprint

Push the repository, then create a Render Blueprint from `render.yaml`. It
defines a web service and a five-minute Myfxbook worker. Fill every environment
variable marked `sync: false` in Render.

The web service needs:

| Variable | Value |
| --- | --- |
| `DJANGO_ALLOWED_HOSTS` | `your-service.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://your-service.onrender.com` |
| `DATABASE_URL` | Neon pooled URL |
| `B2_*` | Values from the previous section |

The worker needs the same `DATABASE_URL` and `DJANGO_SECRET_KEY`, plus
`MYFXBOOK_EMAIL` and `MYFXBOOK_PASSWORD`. They renew the IP-bound Myfxbook
session and are never stored in journal tables or logs.

Render pre-deploy commands are not available on every plan, so the Blueprint
runs idempotent migrations before Gunicorn. On a plan that supports pre-deploy,
move `uv run python manage.py migrate --noinput` there.

## 4. First production login

In the Render Shell:

```bash
uv run python manage.py createsuperuser
```

Then verify:

```text
/health/              returns {"status": "ok"}
/admin/               loads over HTTPS
an uploaded image     resolves through a signed B2 URL
worker logs           report Myfxbook cycles without credentials
```

## Security and operations

Use Render environment settings rather than a committed `.env`. Production
enables HTTPS redirection, secure cookies, HSTS, rate limiting, private media,
and Neon TLS. Never store an MT5 master password; connect IC Markets to
Myfxbook using only the investor/read-only password.

Neon and B2 are separate backup domains: restoring PostgreSQL does not restore
deleted B2 images, and restoring B2 objects does not restore database rows.
Before release, run `python manage.py check --deploy` with production variables.

## Docker alternative

The [`.docker/` guide](../.docker/README.md) provides one immutable image with
separate web and Myfxbook-worker roles plus a local PostgreSQL Compose stack.
Render's native Blueprint remains smaller, while Docker is useful for another
host or reproducible local production checks.
