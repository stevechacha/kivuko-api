from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def root(_request):
    return JsonResponse(
        {
            "service": "kivuko-api",
            "status": "ok",
            "message": "Kivuko la Muungano Hub API",
            "health": "/health/",
            "api": "/api/v1/",
            "admin": "/admin/",
        }
    )


urlpatterns = [
    path("", root, name="root"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("health/", include("api.health_urls")),
]
