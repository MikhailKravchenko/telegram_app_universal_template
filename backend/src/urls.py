from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from src.settings import MEDIA_ROOT, MEDIA_URL


def health_view(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/v1/accounts/", include("src.accounts.urls", namespace="accounts")),
    path("health/", health_view, name="health"),
] + static(MEDIA_URL, document_root=MEDIA_ROOT)
