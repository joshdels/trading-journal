from django.urls import path

from . import views

urlpatterns = [
    path("", views.portal, name="portal"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/month/", views.calendar_month, name="calendar_month"),
    path("calendar/daily/", views.daily_view, name="daily_view"),
    path("calendar/monthly/", views.monthly_view, name="monthly_view"),
    path("calendar/<int:year>/<int:month>/<int:day>/", views.day_trades, name="day_trades"),
    path("charts/", views.charts, name="charts"),
]
