from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import JournalBlockForm, PlanForm, TradeForm, TradeImageUploadForm, TradeReviewForm
from .models import JournalBlock, JournalBlockImage, Strategy, Trade, TradeImage


@login_required
def trade_list(request):
    trades = Trade.objects.filter(account__owner=request.user).select_related("strategy", "account")
    symbol = request.GET.get("symbol", "").strip().upper()
    strategy = request.GET.get("strategy", "").strip()
    if symbol:
        trades = trades.filter(symbol=symbol)
    if strategy:
        trades = trades.filter(strategy_id=strategy)
    symbols = (
        Trade.objects.filter(account__owner=request.user).order_by("symbol").values_list("symbol", flat=True).distinct()
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
        Trade.all_objects.select_related("strategy", "account"), pk=pk, account__owner=request.user
    )
    return render(request, "trades/trade_detail.html", {
        "trade": trade,
        "review_form": TradeReviewForm(instance=getattr(trade, "review", None)),
        "image_form": TradeImageUploadForm(),
        "images_by_stage": _images_by_stage(trade),
        **_journal_context(trade),
    })


def _journal_context(trade):
    blocks = list(
        trade.journal_blocks.prefetch_related("images").all()
    )
    blocks_by_stage = [
        (value, label, [b for b in blocks if b.stage == value])
        for value, label in JournalBlock.Stage.choices
    ]
    return {"blocks_by_stage": blocks_by_stage, "journal_form": JournalBlockForm()}


@login_required
def journal_block_add(request, pk):
    """Append a journal block (note + optional images) to a trade (HTMX)."""
    trade = get_object_or_404(Trade, pk=pk, account__owner=request.user)
    form = JournalBlockForm(request.POST, request.FILES)
    if form.is_valid():
        order = trade.journal_blocks.filter(stage=form.cleaned_data["stage"]).count()
        block = JournalBlock.objects.create(
            trade=trade,
            stage=form.cleaned_data["stage"],
            note=form.cleaned_data.get("note", ""),
            logged_at=form.cleaned_data.get("logged_at") or timezone.now(),
            order=order,
        )
        for i, img in enumerate(form.cleaned_data.get("images") or []):
            JournalBlockImage.objects.create(block=block, image=img, order=i)
    return render(request, "partials/trade_journal.html", {
        "trade": trade, "journal_form": JournalBlockForm(),
        **{k: v for k, v in _journal_context(trade).items() if k != "journal_form"},
    })


@login_required
def journal_block_delete(request, pk, block_id):
    trade = get_object_or_404(Trade, pk=pk, account__owner=request.user)
    JournalBlock.objects.filter(pk=block_id, trade=trade).delete()
    return render(request, "partials/trade_journal.html", {
        "trade": trade, **_journal_context(trade),
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
    trade = get_object_or_404(Trade, pk=pk, account__owner=request.user)
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
    trade = get_object_or_404(Trade, pk=pk, account__owner=request.user)
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
def plan_list(request):
    """Open plans (floating trade ideas) awaiting their real fill."""
    plans = Trade.plans.filter(
        account__owner=request.user, plan_status=Trade.PlanStatus.PLANNED
    ).select_related("account", "strategy")
    realized = Trade.plans.filter(
        account__owner=request.user, plan_status=Trade.PlanStatus.REALIZED
    ).select_related("realized_trade")[:10]
    return render(request, "trades/plan_list.html", {"plans": plans, "realized": realized})


@login_required
def plan_create(request):
    form = PlanForm(request.POST or None)
    # Only the user's own accounts are selectable.
    form.fields["account"].queryset = form.fields["account"].queryset.filter(owner=request.user)
    if request.method == "POST" and form.is_valid():
        plan = form.save(commit=False)
        plan.is_plan = True
        plan.plan_status = Trade.PlanStatus.PLANNED
        plan.status = Trade.Status.OPEN
        plan.confirmed = True  # plans never sit in the import Inbox
        plan.save()
        form.save_m2m()
        return redirect("trade_detail", pk=plan.pk)
    return render(request, "trades/plan_form.html", {"form": form})


@login_required
def trade_review(request, pk):
    """Inline 2-day review form (HTMX-swappable)."""
    trade = get_object_or_404(Trade, pk=pk, account__owner=request.user)
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
