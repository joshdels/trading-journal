from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trades", "0003_trade_unique_mt5_ticket_per_account")]

    operations = [
        migrations.AddField(model_name="trade", name="external_source", field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name="trade", name="external_key", field=models.CharField(blank=True, max_length=80)),
        migrations.AddConstraint(
            model_name="trade",
            constraint=models.UniqueConstraint(condition=models.Q(("external_key__gt", "")), fields=("account", "external_source", "external_key"), name="unique_external_trade_per_account"),
        ),
    ]
