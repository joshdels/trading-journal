from django.urls import path

from . import views

urlpatterns = [
    path("", views.trade_list, name="trade_list"),
    path("new/", views.trade_create, name="trade_create"),
    path("plans/", views.plan_list, name="plan_list"),
    path("plans/new/", views.plan_create, name="plan_create"),
    path("<int:pk>/", views.trade_detail, name="trade_detail"),
    path("<int:pk>/review/", views.trade_review, name="trade_review"),
    path("<int:pk>/images/", views.trade_image_upload, name="trade_image_upload"),
    path("<int:pk>/images/<int:image_id>/delete/", views.trade_image_delete, name="trade_image_delete"),
    path("<int:pk>/journal/add/", views.journal_block_add, name="journal_block_add"),
    path("<int:pk>/journal/<int:block_id>/delete/", views.journal_block_delete, name="journal_block_delete"),
]
