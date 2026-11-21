"""Aggregation helpers for the calendar, charts and portal."""

import calendar as _cal
from collections import defaultdict
from datetime import date

from django.db.models import Count, Sum
from django.utils import timezone

from app.trades.models import Trade


def month_calendar(year, month):
    """Return weeks of day-cells with net P/L and trade count for a month."""
    qs = (
        Trade.objects.filter(
            status=Trade.Status.CLOSED,
            exit_time__year=year,
            exit_time__month=month,
        )
        .values_list("exit_time", "profit", "commission", "swap")
    )
    by_day = defaultdict(lambda: {"pnl": 0.0, "count": 0})
    for exit_time, profit, commission, swap in qs:
        d = timezone.localtime(exit_time).day
        by_day[d]["pnl"] += float(profit) + float(commission) + float(swap)
        by_day[d]["count"] += 1

    cal = _cal.Calendar(firstweekday=6)  # Sunday-first, like MT5
    weeks = []
    for week in cal.monthdayscalendar(year, month):
        cells = []
        for day in week:
            if day == 0:
                cells.append(None)
            else:
                info = by_day.get(day, {"pnl": 0.0, "count": 0})
                cells.append({"day": day, "pnl": round(info["pnl"], 2), "count": info["count"]})
        weeks.append(cells)
    month_pnl = round(sum(v["pnl"] for v in by_day.values()), 2)
    return weeks, month_pnl


def year_months(year):
    """12 month-cells for a year with aggregated P/L + trade count, plus the
    year total. Used by the calendar's 'Monthly' granularity."""
    buckets = defaultdict(lambda: {"pnl": 0.0, "count": 0})
    qs = Trade.objects.filter(
        status=Trade.Status.CLOSED, exit_time__year=year
    ).values_list("exit_time", "profit", "commission", "swap")
    for exit_time, profit, commission, swap in qs:
        m = timezone.localtime(exit_time).month
        buckets[m]["pnl"] += float(profit) + float(commission) + float(swap)
        buckets[m]["count"] += 1
    cells = []
    for m in range(1, 13):
        v = buckets.get(m, {"pnl": 0.0, "count": 0})
        cells.append({
            "month": m, "label": date(year, m, 1).strftime("%b"),
            "pnl": round(v["pnl"], 2), "count": v["count"],
        })
    year_pnl = round(sum(c["pnl"] for c in cells), 2)
    return cells, year_pnl


def pips_by_pair():
    """Per-symbol summary across closed trades: net pips, trade count, net P/L
    and wins — the pairs you've actually traded, for the chart."""
    agg = defaultdict(lambda: {"pips": 0.0, "count": 0, "pnl": 0.0, "wins": 0})
    for t in Trade.objects.filter(status=Trade.Status.CLOSED).only(
        "symbol", "direction", "entry_price", "exit_price",
        "profit", "commission", "swap",
    ):
        a = agg[t.symbol]
        p = t.pips
        if p is not None:
            a["pips"] += p
        a["count"] += 1
        a["pnl"] += t.net_profit
        if t.is_win:
            a["wins"] += 1
    rows = [
        {
            "symbol": s, "pips": round(v["pips"], 1), "count": v["count"],
            "pnl": round(v["pnl"], 2), "wins": v["wins"],
            "win_rate": round(v["wins"] / v["count"] * 100) if v["count"] else 0,
        }
        for s, v in agg.items()
    ]
    rows.sort(key=lambda x: x["pips"])
    return rows


def portfolio_stats():
    closed = Trade.objects.filter(status=Trade.Status.CLOSED)
    total = closed.count()
    wins = sum(1 for t in closed.only("profit", "commission", "swap") if t.is_win)
    agg = closed.aggregate(
        pnl=Sum("profit"), comm=Sum("commission"), sw=Sum("swap")
    )
    net = float(agg["pnl"] or 0) + float(agg["comm"] or 0) + float(agg["sw"] or 0)
    return {
        "total_trades": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate": round(wins / total * 100, 1) if total else 0.0,
        "net_pnl": round(net, 2),
        "open_trades": Trade.objects.filter(status=Trade.Status.OPEN).count(),
    }
