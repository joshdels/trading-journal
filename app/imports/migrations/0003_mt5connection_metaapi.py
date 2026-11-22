from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("imports", "0002_mt5connection")]

    operations = [
        migrations.AlterField(model_name="mt5connection", name="token_prefix", field=models.CharField(blank=True, max_length=16, null=True, unique=True)),
        migrations.AlterField(model_name="mt5connection", name="token_hash", field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name="mt5connection", name="metaapi_account_id", field=models.CharField(blank=True, max_length=64, null=True, unique=True)),
        migrations.AddField(model_name="mt5connection", name="region", field=models.CharField(default="new-york", max_length=32)),
        migrations.AddField(model_name="mt5connection", name="state", field=models.CharField(default="not_connected", max_length=32)),
        migrations.AddField(model_name="mt5connection", name="last_history_sync_at", field=models.DateTimeField(blank=True, null=True)),
    ]
