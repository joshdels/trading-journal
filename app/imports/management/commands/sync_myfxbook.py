import time

from django.conf import settings
from django.core.management.base import BaseCommand

from app.imports.models import MT5Connection
from app.imports.services import sync_myfxbook_connection


class Command(BaseCommand):
    help = "Synchronize every enabled Myfxbook connection."

    def add_arguments(self, parser):
        parser.add_argument(
            "--watch", action="store_true",
            help="Keep running and poll at the configured interval (five minutes by default).",
        )
        parser.add_argument(
            "--interval", type=int, default=settings.MYFXBOOK_SYNC_INTERVAL_SECONDS,
            help="Seconds between polls in watch mode; minimum 60.",
        )

    def handle(self, *args, **options):
        interval = max(options["interval"], 60)
        while True:
            self._sync_once()
            if not options["watch"]:
                return
            self.stdout.write(f"Next Myfxbook check in {interval} seconds.")
            time.sleep(interval)

    def _sync_once(self):
        connections = MT5Connection.objects.filter(
            enabled=True,
            myfxbook_account_id__isnull=False,
        ).select_related("account")
        succeeded = failed = 0
        for connection in connections:
            try:
                result = sync_myfxbook_connection(connection)
                succeeded += 1
                self.stdout.write(self.style.SUCCESS(
                    f"{connection.account}: {result['positions']} open, "
                    f"{result['pending_orders']} pending, "
                    f"{result['history']} recent history, {result['created']} created"
                ))
            except Exception as exc:
                failed += 1
                connection.last_error = str(exc)[:1000]
                connection.state = "error"
                connection.save(update_fields=["last_error", "state"])
                self.stderr.write(self.style.ERROR(f"{connection.account}: {exc}"))
        self.stdout.write(f"Myfxbook sync complete: {succeeded} succeeded, {failed} failed")
