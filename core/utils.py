"""Shared helper functions used across apps."""

from datetime import date, timedelta


def week_bounds(d: date):
    """Return (monday, sunday) for the week containing date d."""
    monday = d - timedelta(days=d.weekday())
    return monday, monday + timedelta(days=6)


def pnl_class(value) -> str:
    """CSS class for a signed number: 'pos' / 'neg'."""
    try:
        return "pos" if float(value) >= 0 else "neg"
    except (TypeError, ValueError):
        return "muted"
