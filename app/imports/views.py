from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from app.accounts.models import TradingAccount
from app.journal.models import WeeklyReview
from app.trades.models import Trade
from core.lib.mt5.myfxbook import MyfxbookClient, MyfxbookError
from core.lib.mt5.parsers import CsvParser

from .models import ImportBatch, MT5Connection
from .services import import_rows, link_plan_to_trade, sync_myfxbook_connection


class UploadForm(forms.Form):
    account = forms.ModelChoiceField(queryset=TradingAccount.objects.none())
    file = forms.FileField(help_text="MT5 deal-history CSV export")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = TradingAccount.objects.filter(owner=user)


class MyfxbookLoginForm(forms.Form):
    email = forms.EmailField(label="Myfxbook email")
    password = forms.CharField(
        label="Myfxbook password", widget=forms.PasswordInput,
        help_text="Used once to create an IP-bound API session; never stored.",
    )


class MyfxbookAccountForm(forms.Form):
    account = forms.ChoiceField(label="Myfxbook account")

    def __init__(self, accounts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].choices = [
            (str(item["id"]), f"{item.get('name', 'MT5 Account')} · {item.get('accountId', '')}")
            for item in accounts
        ]


def _unconfirmed_trades(user):
    return (
        Trade.objects.filter(account__owner=user, confirmed=False)
        .select_related("account", "strategy")
        .order_by("-entry_time")
    )


def _suggest_plan(trade, open_plans):
    """Best open plan matching a booked trade: same symbol+direction, entry
    within 3 days. Closest entry time wins. Returns None if nothing fits."""
    window = timedelta(days=3)
    candidates = [
        p for p in open_plans
        if p.symbol == trade.symbol
        and p.direction == trade.direction
        and abs((p.entry_time - trade.entry_time).total_seconds()) <= window.total_seconds()
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda p: abs((p.entry_time - trade.entry_time).total_seconds()))


@login_required
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def inbox(request):
    """Action center for synced trades, post-analysis, and weekly review."""
    form = UploadForm(request.user, request.POST or None, request.FILES or None)
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
            f"({batch.rows_skipped} duplicates skipped). Review them below.",
        )
        return redirect("inbox")
    pending = list(_unconfirmed_trades(request.user))
    open_plans = list(
        Trade.plans.filter(
            account__owner=request.user, plan_status=Trade.PlanStatus.PLANNED
        ).select_related("account", "strategy").order_by("-entry_time")
    )
    # Pair each pending trade with its best open-plan suggestion (if any).
    pending_rows = [(t, _suggest_plan(t, open_plans)) for t in pending]
    due_reviews = list(
        Trade.objects.filter(
            account__owner=request.user,
            status=Trade.Status.CLOSED,
            review_completed=False,
            review_due_at__lte=timezone.now(),
        ).select_related("account").order_by("review_due_at")[:8]
    )
    today = timezone.localdate()
    is_weekend = today.weekday() >= 5
    week_ending = today + timedelta(days=(6 - today.weekday()) % 7)
    weekly_review_due = is_weekend and not WeeklyReview.objects.filter(
        week_ending=week_ending
    ).exists()
    return render(request, "imports/inbox.html", {
        "form": form,
        "pending_rows": pending_rows,
        "pending_count": len(pending),
        "open_plans": open_plans,
        "due_reviews": due_reviews,
        "weekly_review_due": weekly_review_due,
        "week_ending": week_ending,
        "action_count": len(pending) + len(due_reviews) + int(weekly_review_due),
        "batches": ImportBatch.objects.filter(
            account__owner=request.user
        ).select_related("account")[:10],
    })


@login_required
@require_POST
def inbox_confirm(request):
    """Confirm one trade (?trade=<pk>) or all pending, clearing them from the Inbox."""
    qs = _unconfirmed_trades(request.user)
    trade_id = request.POST.get("trade")
    if trade_id:
        qs = qs.filter(pk=trade_id)
    count = qs.update(confirmed=True)
    messages.success(request, f"Confirmed {count} trade{'' if count == 1 else 's'}.")
    return redirect("inbox")


@login_required
@require_POST
def inbox_link(request):
    """Link a plan to its realised booked trade: merge the captured moment onto
    the real trade and archive the plan. Both must belong to the user."""
    trade = get_object_or_404(
        Trade.objects, pk=request.POST.get("trade"),
        account__owner=request.user, confirmed=False,
    )
    plan = get_object_or_404(
        Trade.plans, pk=request.POST.get("plan"),
        account__owner=request.user, plan_status=Trade.PlanStatus.PLANNED,
    )
    link_plan_to_trade(plan, trade)
    messages.success(
        request,
        f"Linked your {plan.symbol} plan to the booked trade and confirmed it.",
    )
    return redirect("inbox")


@login_required
def mt5_connection(request):
    """Exchange Myfxbook credentials for a session and select an account."""
    login_form = MyfxbookLoginForm(request.POST or None)
    account_form = None
    pending_accounts = request.session.get("myfxbook_pending_accounts", [])
    if request.method == "POST" and request.POST.get("action") == "login" and login_form.is_valid():
        try:
            client = MyfxbookClient()
            session = client.login(login_form.cleaned_data["email"], login_form.cleaned_data["password"])
            pending_accounts = client.accounts(session)
            request.session["myfxbook_pending_session"] = session
            request.session["myfxbook_pending_accounts"] = pending_accounts
            account_form = MyfxbookAccountForm(pending_accounts)
            if not pending_accounts:
                messages.error(request, "No Myfxbook accounts were found. Connect your MT5 account in Myfxbook first.")
        except MyfxbookError as exc:
            messages.error(request, str(exc))
    elif request.method == "POST" and request.POST.get("action") == "select":
        account_form = MyfxbookAccountForm(pending_accounts, request.POST)
        if account_form.is_valid():
            selected = next(
                item for item in pending_accounts if str(item["id"]) == account_form.cleaned_data["account"]
            )
            server_data = selected.get("server") or {}
            server = server_data.get("name", "") if isinstance(server_data, dict) else str(server_data)
            broker_login = str(selected.get("accountId", ""))
            account = TradingAccount.objects.filter(owner=request.user, login=broker_login).first()
            if account is None:
                account = TradingAccount.objects.create(
                    owner=request.user,
                    name=selected.get("name") or f"MT5 {broker_login}",
                    broker=selected.get("broker", ""),
                    login=broker_login,
                    server=server,
                    currency=selected.get("currency") or "USD",
                    is_default=not TradingAccount.objects.filter(owner=request.user).exists(),
                )
            connection, _ = MT5Connection.objects.update_or_create(
                account=account,
                defaults={
                    "myfxbook_account_id": str(selected["id"]),
                    "myfxbook_session": request.session["myfxbook_pending_session"],
                    "session_expires_at": timezone.now() + timedelta(days=29),
                    "state": "connected",
                    "enabled": True,
                    "last_error": "",
                },
            )
            request.session.pop("myfxbook_pending_session", None)
            request.session.pop("myfxbook_pending_accounts", None)
            try:
                result = sync_myfxbook_connection(connection)
                messages.success(request, f"Myfxbook connected. Imported {result['created']} trades.")
            except MyfxbookError as exc:
                messages.warning(request, f"Connected, but the first sync failed: {exc}")
            return redirect("mt5_connection")
    connections = MT5Connection.objects.filter(account__owner=request.user).select_related("account")
    return render(request, "imports/mt5_connection.html", {
        "login_form": login_form,
        "account_form": account_form,
        "connections": connections,
    })


@login_required
@require_POST
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def mt5_sync(request, connection_id):
    try:
        connection = MT5Connection.objects.select_related("account").get(
            pk=connection_id, account__owner=request.user, enabled=True
        )
    except MT5Connection.DoesNotExist:
        messages.error(request, "MT5 connection not found.")
        return redirect("mt5_connection")
    try:
        result = sync_myfxbook_connection(connection)
        messages.success(
            request,
            f"MT5 synchronized: {result['positions']} open, {result['pending_orders']} pending, "
            f"{result['created']} new, {result['updated']} updated.",
        )
    except (MyfxbookError, ValueError, TypeError) as exc:
        connection.last_error = str(exc)[:1000]
        connection.save(update_fields=["last_error"])
        messages.error(request, str(exc))
    return redirect("mt5_connection")
