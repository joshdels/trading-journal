from django import forms

from app.journal.models import TradeReview

from .models import Trade, TradeImage


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """A FileField that accepts several files from one <input multiple>."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)]


class TradeImageUploadForm(forms.Form):
    stage = forms.ChoiceField(choices=TradeImage.Stage.choices)
    caption = forms.CharField(max_length=160, required=False)
    images = MultipleFileField(help_text="Select one or more images")


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
