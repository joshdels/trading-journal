from django.urls import path

from .views import JournalLogoutView, RateLimitedLoginView

urlpatterns = [
    path("login/", RateLimitedLoginView.as_view(), name="login"),
    path("logout/", JournalLogoutView.as_view(), name="logout"),
]
