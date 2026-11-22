from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from app.trades.models import Trade

from .services import month_calendar, pips_by_pair, portfolio_stats, year_months


@login_required
def portal(request):
    stats = portfolio_stats()
    recent = Trade.objects.select_related("strategy", "account")[:8]
    due = Trade.objects.filter(
        status=Trade.Status.CLOSED,
        review_completed=False,
        review_due_at__lte=timezone.now(),
    ).select_related("strategy")[:5]
    today = timezone.localtime()
    weeks, month_pnl = month_calendar(today.year, today.month)
    return render(request, "analytics/portal.html", {
        "stats": stats,
        "recent": recent,
        "due": due,
        "weeks": weeks,
        "month_pnl": month_pnl,
        "cal_year": today.year,
        "cal_month": today.month,
        "cal_label": today.strftime("%B %Y"),
    })


@login_required
def calendar_view(request):
    today = timezone.localtime()
    ctx = _cal_context(today.year, today.month)
    return render(request, "analytics/calendar.html", ctx)


@login_required
def daily_view(request):
    """HTMX partial: the daily #cal-view (month grid + day panel)."""
    today = timezone.localtime()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    return render(request, "partials/daily_view.html", _cal_context(year, month))


@login_required
def calendar_month(request):
    """HTMX partial: swap the calendar grid for a given year/month."""
    year = int(request.GET.get("year"))
    month = int(request.GET.get("month"))
    return render(request, "partials/calendar_grid.html", _cal_context(year, month))


def _cal_context(year, month):
    weeks, month_pnl = month_calendar(year, month)
    prev_month = (month - 1) or 12
    prev_year = year - 1 if month == 1 else year
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year
    return {
        "weeks": weeks,
        "month_pnl": month_pnl,
        "cal_year": year,
        "cal_month": month,
        "cal_label": date(year, month, 1).strftime("%B %Y"),
        "prev_year": prev_year, "prev_month": prev_month,
        "next_year": next_year, "next_month": next_month,
    }


@login_required
def day_trades(request, year, month, day):
    """HTMX partial: trades closed on a specific day."""
    trades = Trade.objects.filter(
        status=Trade.Status.CLOSED,
        exit_time__year=year, exit_time__month=month, exit_time__day=day,
    ).select_related("strategy")
    return render(request, "partials/day_trades.html", {
        "trades": trades, "day_label": date(year, month, day).strftime("%A, %d %B %Y"),
    })


@login_required
def monthly_view(request):
    """HTMX partial: the monthly #cal-view (12-month grid for a year)."""
    today = timezone.localtime()
    year = int(request.GET.get("year", today.year))
    cells, year_pnl = year_months(year)
    return render(request, "partials/monthly_view.html", {
        "cells": cells, "year_pnl": year_pnl, "cal_year": year,
        "prev_year": year - 1, "next_year": year + 1,
    })


# Stable palette for the donut segments (one colour per pair slice).
_DONUT_COLORS = [
    "#22c55e", "#38bdf8", "#f59e0b", "#a78bfa", "#ef4444",
    "#2dd4bf", "#fb7185", "#eab308", "#818cf8", "#f97316",
    "#10b981", "#60a5fa",
]


@login_required
def charts(request):
    pairs = pips_by_pair()
    max_abs = max((abs(p["pips"]) for p in pairs), default=1) or 1

    # Donut of trade-count distribution per pair (always non-negative).
    total_trades = sum(p["count"] for p in pairs) or 1
    segments, stops, acc = [], [], 0.0
    for i, p in enumerate(sorted(pairs, key=lambda x: -x["count"])):
        color = _DONUT_COLORS[i % len(_DONUT_COLORS)]
        share = p["count"] / total_trades * 100
        start, acc = acc, acc + share
        stops.append(f"{color} {start:.2f}% {acc:.2f}%")
        segments.append({
            "symbol": p["symbol"], "count": p["count"], "pnl": p["pnl"],
            "color": color, "pct": round(share),
        })
    donut_gradient = "conic-gradient(" + ", ".join(stops) + ")" if segments else ""

    return render(request, "analytics/charts.html", {
        "pairs": pairs, "max_abs": max_abs,
        "donut_segments": segments, "donut_gradient": donut_gradient,
        "total_trades": sum(p["count"] for p in pairs),
    })
