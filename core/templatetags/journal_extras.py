"""Shared template filters/tags for the journal UI."""

from django import template
from django.utils.safestring import mark_safe

from core.utils import pnl_class as _pnl_class

register = template.Library()

_SYMBOL_MARKS = {
    "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "JPY": "🇯🇵",
    "AUD": "🇦🇺", "NZD": "🇳🇿", "CAD": "🇨🇦", "CHF": "🇨🇭",
    "XAU": "🪙", "XAG": "◉", "BTC": "₿", "ETH": "Ξ",
}

_SYMBOL_FLAGS = {
    "USD": "us", "EUR": "eu", "GBP": "gb", "JPY": "jp",
    "AUD": "au", "NZD": "nz", "CAD": "ca", "CHF": "ch",
}


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


@register.filter
def symbol_picture(symbol):
    """Return a compact two-part visual marker for an MT5 symbol."""
    clean = "".join(char for char in str(symbol).upper() if char.isalpha())
    base, quote = clean[:3], clean[3:6]
    left = _SYMBOL_MARKS.get(base, base[:1] or "•")
    right = _SYMBOL_MARKS.get(quote, quote[:1] or "")
    return f"{left}{right}"


def _symbol_codes(symbol):
    clean = "".join(char for char in str(symbol).upper() if char.isalpha())
    return clean[:3], clean[3:6]


@register.filter
def symbol_base_picture(symbol):
    base, _ = _symbol_codes(symbol)
    return _SYMBOL_MARKS.get(base, base[:1] or "•")


@register.filter
def symbol_quote_picture(symbol):
    _, quote = _symbol_codes(symbol)
    return _SYMBOL_MARKS.get(quote, quote[:1] or "•")


@register.filter
def symbol_base_flag(symbol):
    base, _ = _symbol_codes(symbol)
    return _SYMBOL_FLAGS.get(base, "")


@register.filter
def symbol_quote_flag(symbol):
    _, quote = _symbol_codes(symbol)
    return _SYMBOL_FLAGS.get(quote, "")


@register.filter
def symbol_base_code(symbol):
    base, _ = _symbol_codes(symbol)
    return base.lower()


# Currency code -> ISO 3166 country for flag-icons, plus metals rendered as
# coloured coin badges instead of a flag.
_CCY_COUNTRY = {
    "USD": "us", "EUR": "eu", "GBP": "gb", "JPY": "jp", "AUD": "au",
    "NZD": "nz", "CAD": "ca", "CHF": "ch", "CNH": "cn", "CNY": "cn",
    "HKD": "hk", "SGD": "sg", "SEK": "se", "NOK": "no", "MXN": "mx",
    "ZAR": "za", "TRY": "tr", "PLN": "pl", "DKK": "dk",
}
_METAL = {
    "XAU": ("Au", "#d4af37"),  # gold
    "XAG": ("Ag", "#c0c0c0"),  # silver
    "XPT": ("Pt", "#8fd0d6"),  # platinum
    "XPD": ("Pd", "#9fb0c0"),  # palladium
}


def _ccy_badge(code):
    """One circular badge for a currency or metal code."""
    if code in _METAL:
        label, color = _METAL[code]
        return (
            f'<span class="ccy-badge metal" title="{code}" '
            f'style="--metal:{color}">{label}</span>'
        )
    country = _CCY_COUNTRY.get(code)
    if country:
        return (
            f'<span class="ccy-badge"><span class="fi fi-{country}" '
            f'title="{code}"></span></span>'
        )
    # Unknown code: show the first two letters on a neutral badge.
    return f'<span class="ccy-badge metal" style="--metal:#475569">{code[:2]}</span>'


@register.filter
def pair_logo(symbol):
    """Overlapping circular flag badges for a trading symbol, e.g.
    EURUSD -> EU + US flags, XAUUSD -> gold coin + US flag."""
    if not symbol:
        return ""
    s = str(symbol).upper().replace("/", "").replace(".", "").replace("-", "")
    base, quote = s[:3], s[3:6]
    parts = [_ccy_badge(base)]
    if quote:
        parts.append(_ccy_badge(quote))
    return mark_safe(f'<span class="pair-logo">{"".join(parts)}</span>')


@register.simple_tag
def icon(name, extra=""):
    """Render a Phosphor icon: {% icon 'chart-line-up' %}."""
    cls = f"ph ph-{name}" + (f" {extra}" if extra else "")
    return mark_safe(f'<i class="{cls}"></i>')
