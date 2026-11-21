"""App-facing AI review hook. Delegates to the external backend in api.ai."""

from django.utils import timezone

from api.ai.backends import get_backend


def request_review(trade):
    """Mark a trade for AI review and run the (currently null) backend."""
    trade.ai_review_requested_at = timezone.now()
    trade.ai_review = get_backend().generate_review(trade)
    trade.save(update_fields=["ai_review", "ai_review_requested_at"])
    return trade.ai_review
