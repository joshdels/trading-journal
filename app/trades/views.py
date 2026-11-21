from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TradeForm, TradeImageUploadForm, TradeReviewForm
from .models import Strategy, Trade, TradeImage


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
        "image_form": TradeImageUploadForm(),
        "images_by_stage": _images_by_stage(trade),
    })


def _images_by_stage(trade):
    images = list(trade.images.all())
    return [
        (label, [i for i in images if i.stage == value])
        for value, label in TradeImage.Stage.choices
    ]


@login_required
def trade_image_upload(request, pk):
    """Attach one or more images to a trade at a given stage (HTMX)."""
    trade = get_object_or_404(Trade, pk=pk)
    form = TradeImageUploadForm(request.POST, request.FILES)
    if form.is_valid():
        start = trade.images.filter(stage=form.cleaned_data["stage"]).count()
        for i, img in enumerate(form.cleaned_data["images"]):
            TradeImage.objects.create(
                trade=trade, image=img, stage=form.cleaned_data["stage"],
                caption=form.cleaned_data["caption"], order=start + i,
            )
    return render(request, "partials/trade_images.html", {
        "trade": trade,
        "image_form": TradeImageUploadForm(),
        "images_by_stage": _images_by_stage(trade),
    })


@login_required
def trade_image_delete(request, pk, image_id):
    trade = get_object_or_404(Trade, pk=pk)
    TradeImage.objects.filter(pk=image_id, trade=trade).delete()
    return render(request, "partials/trade_images.html", {
        "trade": trade,
        "image_form": TradeImageUploadForm(),
        "images_by_stage": _images_by_stage(trade),
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
