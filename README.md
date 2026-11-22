# Trading Journal

A private Django trading journal for MT5 workflows. It combines manual/CSV
imports with delayed Myfxbook cloud synchronization, an Inbox for newly synced
trades, P/L analytics, screenshots, and structured trade reviews.

## Highlights

- Responsive Django + HTMX interface using Flowbite and Phosphor icons.
- Trade journal with screenshots, strategies, tags, reviews, and weekly notes.
- Calendar, portfolio metrics, pair performance, and review notifications.
- Myfxbook polling every five minutes for freshest-available open and closed trades.
- Production-ready configuration for Render, Neon PostgreSQL, and private Backblaze B2 media.

## Local setup

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

Open `http://127.0.0.1:8000`. The demo command prints the generated credentials;
change the password before using real trading data.

```bash
uv run pytest
uv run python manage.py check
```

## Production

The included [`render.yaml`](render.yaml) defines the Django web service and the
Myfxbook synchronization worker. Production data belongs in Neon; uploaded trade
screenshots belong in a private B2 bucket.

- [Deployment: Render + Neon + B2](docs/deployment.md)
- [Myfxbook and CSV synchronization](docs/mt5-import.md)
- [Project architecture](docs/architecture.md)
- [Docker option](.docker/README.md)

## Important limitation

Myfxbook is not real-time and exposes only its latest 50 history transactions.
The worker polls every five minutes and permanently retains records it observes;
use a one-time CSV import for older history.
