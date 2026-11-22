from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from core.views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("", include("app.accounts.urls")),
    path("", include("app.analytics.urls")),
    path("trades/", include("app.trades.urls")),
    path("journal/", include("app.journal.urls")),
    path("inbox/", include("app.imports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
