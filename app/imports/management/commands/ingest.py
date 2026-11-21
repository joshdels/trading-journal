"""Ingest an MT5 CSV deal export from the command line.

    python manage.py ingest history.csv
    python manage.py ingest history.csv --account "Demo (seeded)"

Idempotent: duplicate tickets are skipped.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from api.mt5.parsers import CsvParser
from app.accounts.models import TradingAccount
from app.imports.services import import_rows


class Command(BaseCommand):
    help = "Import an MT5 CSV deal export into a trading account."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the MT5 CSV export")
        parser.add_argument(
            "--account",
            help="Account name (defaults to the account marked default, else the first)",
        )

    def handle(self, *args, **opts):
        path = Path(opts["path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        account = self._pick_account(opts.get("account"))
        with path.open("rb") as fh:
            rows = CsvParser().parse(fh)
        batch = import_rows(account, rows, kind="csv", source_name=path.name)

        self.stdout.write(self.style.SUCCESS(
            f"Ingested {batch.rows_created} trades into '{account.name}' "
            f"({batch.rows_skipped} duplicates skipped, {batch.rows_parsed} parsed)."
        ))

    @staticmethod
    def _pick_account(name):
        qs = TradingAccount.objects.all()
        if name:
            account = qs.filter(name=name).first()
            if not account:
                raise CommandError(f"No account named '{name}'.")
            return account
        account = qs.filter(is_default=True).first() or qs.first()
        if not account:
            raise CommandError("No trading account exists. Create one first (admin or seed_demo).")
        return account
