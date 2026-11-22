from django.urls import path

from . import views

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("confirm/", views.inbox_confirm, name="inbox_confirm"),
    path("link/", views.inbox_link, name="inbox_link"),
    path("mt5/", views.mt5_connection, name="mt5_connection"),
    path("mt5/<int:connection_id>/sync/", views.mt5_sync, name="mt5_sync"),
]
