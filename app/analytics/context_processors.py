from datetime import timedelta

from django.utils import timezone

from app.trades.models import Trade
from app.journal.models import WeeklyReview


def pending_reviews(request):
    """Expose the current user's review and newly-opened-trade inbox."""
    if not request.user.is_authenticated:
        return {}
    due_reviews = Trade.objects.filter(
        account__owner=request.user,
        status=Trade.Status.CLOSED,
        review_completed=False,
        review_due_at__lte=timezone.now(),
    ).order_by("review_due_at")
    new_open_trades = Trade.objects.filter(
        account__owner=request.user,
        status=Trade.Status.OPEN,
        source=Trade.Source.IMPORT,
        external_source="myfxbook",
        created_at__gte=timezone.now() - timedelta(hours=24),
    ).select_related("account").order_by("-created_at")
    reviews_count = due_reviews.count()
    open_count = new_open_trades.count()
    synced_count = Trade.objects.filter(
        account__owner=request.user, confirmed=False
    ).count()
    # Saturday=5, Sunday=6
    is_weekend = timezone.localtime().weekday() >= 5
    today = timezone.localdate()
    week_ending = today + timedelta(days=(6 - today.weekday()) % 7)
    weekly_due = is_weekend and not WeeklyReview.objects.filter(week_ending=week_ending).exists()
    return {
        "reviews_due_count": due_reviews.count(),
        "review_notifications": due_reviews[:6],
        "open_trade_notifications_count": open_count,
        "open_trade_notifications": new_open_trades[:6],
        "inbox_notification_count": reviews_count + open_count,
        "inbox_count": synced_count + reviews_count + int(weekly_due),
        "is_weekend": is_weekend,
    }
