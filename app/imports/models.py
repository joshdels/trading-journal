from django.db import models


class ImportBatch(models.Model):
    """Audit record for one MT5 history import. Makes re-imports traceable."""

    class Kind(models.TextChoices):
        CSV = "csv", "CSV"
        HTML = "html", "HTML report"
        LIVE = "live", "Live MT5 sync"

    account = models.ForeignKey(
        "accounts.TradingAccount", on_delete=models.CASCADE, related_name="imports"
    )
    kind = models.CharField(max_length=5, choices=Kind.choices)
    source_name = models.CharField(max_length=255, blank=True)
    rows_parsed = models.PositiveIntegerField(default=0)
    rows_created = models.PositiveIntegerField(default=0)
    rows_skipped = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.rows_created} created ({self.created_at:%Y-%m-%d})"


class MT5Connection(models.Model):
    """Myfxbook API session mapped to one journal trading account."""

    account = models.OneToOneField(
        "accounts.TradingAccount", on_delete=models.CASCADE, related_name="mt5_connection"
    )
    state = models.CharField(max_length=32, default="not_connected")
    last_history_sync_at = models.DateTimeField(null=True, blank=True)
    myfxbook_account_id = models.CharField(max_length=64, unique=True, blank=True, null=True)
    myfxbook_session = models.TextField(blank=True)
    session_expires_at = models.DateTimeField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Myfxbook sync — {self.account}"
