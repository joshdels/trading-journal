from django.urls import path

from . import views

urlpatterns = [
    path("weekly/", views.weekly_list, name="weekly_list"),
]
