from django.db import connection
from django.http import JsonResponse


def health(request):
    """Render health check: Django and its configured database are ready."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ok"})
