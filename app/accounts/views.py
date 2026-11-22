from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit


@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True), name="post"
)
class RateLimitedLoginView(auth_views.LoginView):
    """Login throttled to 5 POSTs/min per IP — blunts credential-stuffing.

    In production Cloudflare fronts the app and provides the real client IP
    (see docs/deployment.md); here the direct IP is used.
    """

    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {form.get_user().username}.")
        return response


class JournalLogoutView(auth_views.LogoutView):
    """Sign out through a CSRF-protected POST and confirm the session ended."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been signed out safely.")
        return response
