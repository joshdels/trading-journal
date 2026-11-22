"""Project-wide globals. Single source of truth for shared values."""

SITE_NAME = "Trading Journal"
VERSION = "0.1.0"

# The MT5 theme palette, mirrored from static/css/theme.css so Python-side
# code (charts, emails) can reference the same colours.
COLORS = {
    "green": "#26a69a",
    "red": "#ef5350",
    "accent": "#42a5f5",
    "warn": "#f0a202",
    "muted": "#8a8a8a",
}

# Days after a trade's exit before its post-trade review opens.
REVIEW_DELAY_DAYS = 2
