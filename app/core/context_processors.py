from .constants import SITE_NAME, VERSION


def site_globals(request):
    """Site-wide template globals available on every page."""
    return {"SITE_NAME": SITE_NAME, "VERSION": VERSION}
