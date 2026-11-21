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
