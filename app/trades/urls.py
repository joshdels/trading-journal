from django.urls import path

from . import views

urlpatterns = [
    path("", views.trade_list, name="trade_list"),
    path("new/", views.trade_create, name="trade_create"),
    path("<int:pk>/", views.trade_detail, name="trade_detail"),
    path("<int:pk>/review/", views.trade_review, name="trade_review"),
]
