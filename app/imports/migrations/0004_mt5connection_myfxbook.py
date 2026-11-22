from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("imports", "0003_mt5connection_metaapi")]

    operations = [
        migrations.AddField(model_name="mt5connection", name="myfxbook_account_id", field=models.CharField(blank=True, max_length=64, null=True, unique=True)),
        migrations.AddField(model_name="mt5connection", name="myfxbook_session", field=models.TextField(blank=True)),
        migrations.AddField(model_name="mt5connection", name="session_expires_at", field=models.DateTimeField(blank=True, null=True)),
    ]
