from django.contrib.auth import views as auth_views
from django.urls import path

from .views import RateLimitedLoginView

urlpatterns = [
    path("login/", RateLimitedLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
