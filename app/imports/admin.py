from django.contrib import admin

from .models import ImportBatch, MT5Connection

admin.site.register(ImportBatch)
admin.site.register(MT5Connection)
