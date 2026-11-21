from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TradeForm, TradeReviewForm
from .models import Strategy, Trade


@login_required
def trade_list(request):
    trades = Trade.objects.select_related("strategy", "account")
    symbol = request.GET.get("symbol", "").strip().upper()
    strategy = request.GET.get("strategy", "").strip()
    if symbol:
        trades = trades.filter(symbol=symbol)
    if strategy:
        trades = trades.filter(strategy_id=strategy)
    symbols = (
        Trade.objects.order_by("symbol").values_list("symbol", flat=True).distinct()
    )
    return render(request, "trades/trade_list.html", {
        "trades": trades,
        "symbols": symbols,
        "strategies": Strategy.objects.all(),
        "active_symbol": symbol,
        "active_strategy": strategy,
    })


@login_required
def trade_detail(request, pk):
    trade = get_object_or_404(
        Trade.objects.select_related("strategy", "account"), pk=pk
    )
    return render(request, "trades/trade_detail.html", {
        "trade": trade,
        "review_form": TradeReviewForm(instance=getattr(trade, "review", None)),
    })


@login_required
def trade_create(request):
    form = TradeForm(request.POST or None)
    if form.is_valid():
        trade = form.save()
        return redirect("trade_detail", pk=trade.pk)
    return render(request, "trades/trade_form.html", {"form": form})


@login_required
def trade_review(request, pk):
    """Inline 2-day review form (HTMX-swappable)."""
    trade = get_object_or_404(Trade, pk=pk)
    review = getattr(trade, "review", None)
    form = TradeReviewForm(request.POST or None, instance=review)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.trade = trade
        review.save()
        trade.review_completed = True
        trade.save(update_fields=["review_completed"])
        return render(request, "partials/review_done.html", {"trade": trade})
    return render(request, "partials/review_form.html", {"trade": trade, "form": form})
