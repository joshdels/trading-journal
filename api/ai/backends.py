"""
External AI-review backends. This is the integration boundary — code here is
what talks OUT to an AI provider. Nothing is wired yet.

When you enable AI review, implement `generate_review` in a concrete backend
(e.g. a Claude API call) and return it from `get_backend`. The app layer
(app.ai_review.services) is the only caller, so nothing else changes.
"""


class AIReviewBackend:
    """Base interface. Subclass and implement generate_review()."""

    def generate_review(self, trade) -> str:
        raise NotImplementedError


class NullBackend(AIReviewBackend):
    """Default: produces no text. Keeps the feature inert until configured."""

    def generate_review(self, trade) -> str:
        return ""


def get_backend() -> AIReviewBackend:
    # Swap for a configured provider backend when AI review is turned on.
    return NullBackend()
