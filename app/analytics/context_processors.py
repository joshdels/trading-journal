from django.utils import timezone

from app.trades.models import Trade


def pending_reviews(request):
    """Expose overdue-review count + weekend flag to every template."""
    if not request.user.is_authenticated:
        return {}
    due = Trade.objects.filter(
        status=Trade.Status.CLOSED,
        review_completed=False,
        review_due_at__lte=timezone.now(),
    ).count()
    # Saturday=5, Sunday=6
    is_weekend = timezone.localtime().weekday() >= 5
    return {"reviews_due_count": due, "is_weekend": is_weekend}
