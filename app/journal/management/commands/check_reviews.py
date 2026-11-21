"""
Surface what's due for review. In-app model: this prints a summary and is
safe to wire to cron later. The portal badge is driven by the same query via
analytics.context_processors, so nothing here needs to send a notification.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from app.trades.models import Trade


class Command(BaseCommand):
    help = "Report overdue 2-day trade reviews and weekend review status."

    def handle(self, *args, **opts):
        now = timezone.now()
        due = Trade.objects.filter(
            status=Trade.Status.CLOSED,
            review_completed=False,
            review_due_at__lte=now,
        )
        self.stdout.write(self.style.NOTICE(f"{due.count()} trade(s) due for review:"))
        for t in due[:50]:
            self.stdout.write(f"  #{t.pk} {t.symbol} {t.get_direction_display()} "
                              f"— closed {t.exit_time:%Y-%m-%d}")
        if timezone.localtime().weekday() >= 5:
            self.stdout.write(self.style.WARNING("It's the weekend — time for your weekly review."))
