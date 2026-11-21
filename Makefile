.PHONY: install migrate run test seed

install:
	uv sync

migrate:
	uv run python manage.py migrate

run:
	uv run python manage.py runserver

test:
	uv run pytest

seed:
	uv run python manage.py seed_demo
