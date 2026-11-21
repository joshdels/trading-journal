from django.db import models


class TradeReview(models.Model):
    """The 2-day post-trade review tied to a single trade."""

    class Emotion(models.TextChoices):
        CALM = "calm", "Calm"
        CONFIDENT = "confident", "Confident"
        FEARFUL = "fearful", "Fearful"
        GREEDY = "greedy", "Greedy"
        FRUSTRATED = "frustrated", "Frustrated"

    trade = models.OneToOneField(
        "trades.Trade", on_delete=models.CASCADE, related_name="review"
    )
    followed_plan = models.BooleanField(default=True)
    emotion = models.CharField(max_length=12, choices=Emotion.choices, blank=True)
    what_went_well = models.TextField(blank=True)
    what_went_wrong = models.TextField(blank=True)
    lesson = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(
        default=3, help_text="Execution quality 1-5"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review of {self.trade}"


class WeeklyReview(models.Model):
    """Weekend review covering a trading week."""

    week_ending = models.DateField(unique=True, help_text="Sunday of the week reviewed")
    summary = models.TextField(blank=True)
    what_worked = models.TextField(blank=True)
    adjustments = models.TextField(blank=True)
    best_trade = models.ForeignKey(
        "trades.Trade", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="best_of_weeks",
    )
    worst_trade = models.ForeignKey(
        "trades.Trade", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="worst_of_weeks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-week_ending"]

    def __str__(self):
        return f"Week ending {self.week_ending}"
