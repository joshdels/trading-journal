from datetime import timedelta

from django.db import models
from django.utils import timezone

# Pip size per symbol. JPY pairs and metals use different decimal places.
JPY_PIP = 0.01
DEFAULT_PIP = 0.0001
METAL_PIP = {"XAUUSD": 0.1, "XAGUSD": 0.01}


def pip_size(symbol: str) -> float:
    s = symbol.upper()
    if s in METAL_PIP:
        return METAL_PIP[s]
    if s.endswith("JPY"):
        return JPY_PIP
    return DEFAULT_PIP


class Strategy(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    rules = models.TextField(blank=True, help_text="Entry/exit rules for this setup")

    class Meta:
        verbose_name_plural = "strategies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Trade(models.Model):
    class Direction(models.TextChoices):
        BUY = "buy", "Buy"
        SELL = "sell", "Sell"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    class Source(models.TextChoices):
        IMPORT = "import", "Import"
        MANUAL = "manual", "Manual"

    account = models.ForeignKey(
        "accounts.TradingAccount", on_delete=models.CASCADE, related_name="trades"
    )
    mt5_ticket = models.BigIntegerField(
        null=True, blank=True, unique=True,
        help_text="MT5 deal/position ticket — dedup key for re-imports",
    )
    symbol = models.CharField(max_length=20)
    direction = models.CharField(max_length=4, choices=Direction.choices)
    volume = models.DecimalField(max_digits=10, decimal_places=2, help_text="Lots")

    entry_price = models.DecimalField(max_digits=14, decimal_places=5)
    exit_price = models.DecimalField(max_digits=14, decimal_places=5, null=True, blank=True)
    sl = models.DecimalField(max_digits=14, decimal_places=5, null=True, blank=True)
    tp = models.DecimalField(max_digits=14, decimal_places=5, null=True, blank=True)

    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)

    profit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    swap = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    strategy = models.ForeignKey(
        Strategy, on_delete=models.SET_NULL, null=True, blank=True, related_name="trades"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="trades")
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=6, choices=Status.choices, default=Status.CLOSED)
    source = models.CharField(max_length=6, choices=Source.choices, default=Source.MANUAL)

    # Post-trade review scheduling (2-day queue).
    review_due_at = models.DateTimeField(null=True, blank=True)
    review_completed = models.BooleanField(default=False)

    # AI review hooks — interface reserved, no provider wired yet.
    ai_review = models.TextField(blank=True)
    ai_review_requested_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entry_time"]
        indexes = [
            models.Index(fields=["symbol"]),
            models.Index(fields=["exit_time"]),
        ]

    def __str__(self):
        return f"{self.symbol} {self.get_direction_display()} {self.volume}"

    @property
    def pips(self):
        """Signed pip result. Positive = favourable move for the direction."""
        if self.exit_price is None:
            return None
        delta = float(self.exit_price) - float(self.entry_price)
        if self.direction == self.Direction.SELL:
            delta = -delta
        return round(delta / pip_size(self.symbol), 1)

    @property
    def net_profit(self):
        return float(self.profit) + float(self.commission) + float(self.swap)

    @property
    def is_win(self):
        return self.net_profit > 0

    @property
    def review_overdue(self):
        return (
            self.status == self.Status.CLOSED
            and not self.review_completed
            and self.review_due_at is not None
            and self.review_due_at <= timezone.now()
        )

    def save(self, *args, **kwargs):
        # Schedule the 2-day post-trade review from exit time.
        if self.exit_time and not self.review_due_at:
            self.review_due_at = self.exit_time + timedelta(days=2)
        super().save(*args, **kwargs)


class TradeImage(models.Model):
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="trades/%Y/%m/")
    caption = models.CharField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or f"Image #{self.pk}"
