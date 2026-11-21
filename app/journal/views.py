from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import WeeklyReview


class WeeklyReviewForm(forms.ModelForm):
    class Meta:
        model = WeeklyReview
        fields = ["week_ending", "summary", "what_worked", "adjustments",
                  "best_trade", "worst_trade"]
        widgets = {
            "week_ending": forms.DateInput(attrs={"type": "date"}),
            "summary": forms.Textarea(attrs={"rows": 3}),
            "what_worked": forms.Textarea(attrs={"rows": 2}),
            "adjustments": forms.Textarea(attrs={"rows": 2}),
        }


@login_required
def weekly_list(request):
    form = WeeklyReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("weekly_list")
    return render(request, "journal/weekly_list.html", {
        "reviews": WeeklyReview.objects.select_related("best_trade", "worst_trade"),
        "form": form,
    })
