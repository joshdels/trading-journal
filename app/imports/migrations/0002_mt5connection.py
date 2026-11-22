import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("imports", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="MT5Connection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_prefix", models.CharField(max_length=16, unique=True)),
                ("token_hash", models.CharField(max_length=64)),
                ("enabled", models.BooleanField(default=True)),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="mt5_connection", to="accounts.tradingaccount")),
            ],
        ),
    ]
