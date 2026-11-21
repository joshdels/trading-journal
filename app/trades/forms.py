from django import forms

from app.journal.models import TradeReview

from .models import Trade


class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = [
            "account", "symbol", "direction", "volume", "entry_price", "exit_price",
            "sl", "tp", "entry_time", "exit_time", "profit", "commission", "swap",
            "strategy", "tags", "status", "notes",
        ]
        widgets = {
            "entry_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "exit_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class TradeReviewForm(forms.ModelForm):
    class Meta:
        model = TradeReview
        fields = [
            "followed_plan", "emotion", "what_went_well",
            "what_went_wrong", "lesson", "rating",
        ]
        widgets = {
            "what_went_well": forms.Textarea(attrs={"rows": 2}),
            "what_went_wrong": forms.Textarea(attrs={"rows": 2}),
            "lesson": forms.Textarea(attrs={"rows": 2}),
        }
