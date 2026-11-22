from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trades", "0002_alter_tradeimage_options_tradeimage_created_at_and_more")]

    operations = [
        migrations.AlterField(
            model_name="trade",
            name="mt5_ticket",
            field=models.BigIntegerField(blank=True, help_text="MT5 deal/position ticket — dedup key for re-imports", null=True),
        ),
        migrations.AddConstraint(
            model_name="trade",
            constraint=models.UniqueConstraint(fields=("account", "mt5_ticket"), name="unique_mt5_ticket_per_account"),
        ),
    ]
