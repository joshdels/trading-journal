from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("imports", "0004_mt5connection_myfxbook")]

    operations = [
        migrations.RemoveField(model_name="mt5connection", name="token_prefix"),
        migrations.RemoveField(model_name="mt5connection", name="token_hash"),
        migrations.RemoveField(model_name="mt5connection", name="metaapi_account_id"),
        migrations.RemoveField(model_name="mt5connection", name="region"),
    ]
