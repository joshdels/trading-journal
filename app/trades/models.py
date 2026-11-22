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


class TradeQuerySet(models.QuerySet):
    def real(self):
        return self.filter(is_plan=False)

    def plans(self):
        return self.filter(is_plan=True)


class RealTradeManager(models.Manager):
    """Default manager: excludes planned (floating) trades so they can never
    leak into P/L calendars, charts or totals. Use Trade.all_objects or
    Trade.plans to reach plans deliberately."""

    def get_queryset(self):
        return TradeQuerySet(self.model, using=self._db).filter(is_plan=False)


class AllTradeManager(models.Manager):
    def get_queryset(self):
        return TradeQuerySet(self.model, using=self._db)


class PlanManager(models.Manager):
    def get_queryset(self):
        return TradeQuerySet(self.model, using=self._db).filter(is_plan=True)


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
        null=True, blank=True,
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
    external_source = models.CharField(max_length=20, blank=True)
    external_key = models.CharField(max_length=80, blank=True)

    # Inbox triage: imported/synced trades land unconfirmed and surface in the
    # Inbox until the trader acknowledges them. Manual entries are born True.
    confirmed = models.BooleanField(
        default=True, help_text="False while awaiting triage in the Inbox"
    )

    # --- Plan ("floating" trade) ----------------------------------------
    # A plan captures the moment/thesis before the real fill exists. It never
    # counts toward P/L (excluded by the default manager). When the broker book
    # delivers the real trade, the plan is linked to it and archived.
    class PlanStatus(models.TextChoices):
        PLANNED = "planned", "Planned"
        REALIZED = "realized", "Realized"
        DISCARDED = "discarded", "Discarded"

    is_plan = models.BooleanField(default=False)
    plan_status = models.CharField(
        max_length=9, choices=PlanStatus.choices, default=PlanStatus.PLANNED
    )
    # On a plan: the real Trade it became. On a real trade: reverse is source_plans.
    realized_trade = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="source_plans",
    )

    # Post-trade review scheduling (2-day queue).
    review_due_at = models.DateTimeField(null=True, blank=True)
    review_completed = models.BooleanField(default=False)

    # AI review hooks — interface reserved, no provider wired yet.
    ai_review = models.TextField(blank=True)
    ai_review_requested_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # objects (default) hides plans so analytics/calendar/charts stay truthful;
    # all_objects and plans reach them when needed.
    objects = RealTradeManager()
    all_objects = AllTradeManager()
    plans = PlanManager()

    class Meta:
        base_manager_name = "all_objects"
        ordering = ["-entry_time"]
        indexes = [
            models.Index(fields=["symbol"]),
            models.Index(fields=["exit_time"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["account", "mt5_ticket"],
                name="unique_mt5_ticket_per_account",
            ),
            models.UniqueConstraint(
                fields=["account", "external_source", "external_key"],
                name="unique_external_trade_per_account",
                condition=models.Q(external_key__gt=""),
            ),
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
    class Stage(models.TextChoices):
        ENTRY = "entry", "Entry"
        EXIT = "exit", "Exit"
        POST = "post", "Post-trade"

    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="trades/%Y/%m/")
    stage = models.CharField(max_length=5, choices=Stage.choices, default=Stage.ENTRY)
    caption = models.CharField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["stage", "order", "id"]

    def __str__(self):
        return self.caption or f"{self.get_stage_display()} image #{self.pk}"


class JournalBlock(models.Model):
    """A timestamped log entry in a trade's journal, grouped by stage.

    Wagtail/Notion-style: you append blocks over time. Each block carries an
    optional note and zero or more images, so the journal reads as a log of
    text + screenshots rather than one controlled upload.
    """

    class Stage(models.TextChoices):
        ENTRY = "entry", "Entry"
        EXIT = "exit", "Exit"
        POST = "post", "Post-trade"

    trade = models.ForeignKey(
        Trade, on_delete=models.CASCADE, related_name="journal_blocks"
    )
    stage = models.CharField(max_length=5, choices=Stage.choices, default=Stage.ENTRY)
    note = models.TextField(blank=True)
    logged_at = models.DateTimeField(
        default=timezone.now, help_text="When this was logged (date & time)"
    )
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["logged_at", "order", "id"]

    def __str__(self):
        return f"{self.get_stage_display()} log @ {self.logged_at:%Y-%m-%d %H:%M}"


class JournalBlockImage(models.Model):
    block = models.ForeignKey(
        JournalBlock, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="journal/%Y/%m/")
    caption = models.CharField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or f"Block image #{self.pk}"
