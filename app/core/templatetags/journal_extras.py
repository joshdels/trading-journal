"""Shared template filters/tags for the journal UI."""

from django import template
from django.utils.safestring import mark_safe

from app.core.utils import pnl_class as _pnl_class

register = template.Library()


@register.filter
def pnl_class(value):
    """CSS class for a signed value: pos / neg / muted."""
    return _pnl_class(value)


@register.filter
def money(value, symbol="$"):
    """Format a number as signed money: 1234.5 -> $1,234.50."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return value
    sign = "-" if v < 0 else ""
    return f"{sign}{symbol}{abs(v):,.2f}"


@register.filter
def pips(value):
    """Format a pip figure with a sign and one decimal: +12.0 / -8.0."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{'+' if v >= 0 else ''}{v:.1f}"


@register.simple_tag
def icon(name, extra=""):
    """Render a Phosphor icon: {% icon 'chart-line-up' %}."""
    cls = f"ph ph-{name}" + (f" {extra}" if extra else "")
    return mark_safe(f'<i class="{cls}"></i>')
