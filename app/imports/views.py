from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit

from app.accounts.models import TradingAccount
from api.mt5.parsers import CsvParser

from .models import ImportBatch
from .services import import_rows


class UploadForm(forms.Form):
    account = forms.ModelChoiceField(queryset=TradingAccount.objects.all())
    file = forms.FileField(help_text="MT5 deal-history CSV export")


@login_required
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def upload(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        rows = CsvParser().parse(form.cleaned_data["file"])
        batch = import_rows(
            account=form.cleaned_data["account"],
            rows=rows,
            kind=ImportBatch.Kind.CSV,
            source_name=form.cleaned_data["file"].name,
        )
        messages.success(
            request,
            f"Imported {batch.rows_created} trades "
            f"({batch.rows_skipped} duplicates skipped).",
        )
        return redirect("imports")
    return render(request, "imports/upload.html", {
        "form": form,
        "batches": ImportBatch.objects.select_related("account")[:10],
    })
