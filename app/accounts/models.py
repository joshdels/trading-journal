from django.conf import settings
from django.db import models


class TradingAccount(models.Model):
    """An MT5 trading account. Stores metadata only — never the password."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts"
    )
    name = models.CharField(max_length=80)
    broker = models.CharField(max_length=120, blank=True)
    login = models.CharField(max_length=40, blank=True, help_text="MT5 login number (metadata only)")
    server = models.CharField(max_length=120, blank=True)
    currency = models.CharField(max_length=8, default="USD")
    leverage = models.PositiveIntegerField(default=100)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "name"]

    def __str__(self):
        return f"{self.name} ({self.currency})"
