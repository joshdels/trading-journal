from django.contrib import admin

from .models import JournalBlock, JournalBlockImage, Strategy, Tag, Trade, TradeImage


class TradeImageInline(admin.TabularInline):
    model = TradeImage
    extra = 1


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("symbol", "direction", "volume", "entry_time", "exit_time",
                    "profit", "status", "review_completed")
    list_filter = ("status", "direction", "symbol", "strategy", "review_completed",
                   "is_plan", "plan_status", "confirmed")
    search_fields = ("symbol", "mt5_ticket")
    inlines = [TradeImageInline]

    def get_queryset(self, request):
        # Show plans in the admin too (the default manager hides them).
        return Trade.all_objects.get_queryset()


class JournalBlockImageInline(admin.TabularInline):
    model = JournalBlockImage
    extra = 1


@admin.register(JournalBlock)
class JournalBlockAdmin(admin.ModelAdmin):
    list_display = ("trade", "stage", "logged_at")
    list_filter = ("stage",)
    inlines = [JournalBlockImageInline]


admin.site.register(Strategy)
admin.site.register(Tag)
