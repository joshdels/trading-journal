from django.contrib import admin

from .models import Strategy, Tag, Trade, TradeImage


class TradeImageInline(admin.TabularInline):
    model = TradeImage
    extra = 1


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("symbol", "direction", "volume", "entry_time", "exit_time",
                    "profit", "status", "review_completed")
    list_filter = ("status", "direction", "symbol", "strategy", "review_completed")
    search_fields = ("symbol", "mt5_ticket")
    inlines = [TradeImageInline]


admin.site.register(Strategy)
admin.site.register(Tag)
