from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.static import serve
import os
from django.conf import settings
from django.conf.urls.static import static

# Serve React index.html for admin SPA
react_admin_view = never_cache(TemplateView.as_view(template_name="index.html"))

schema_view = get_schema_view(
    openapi.Info(
        title="Ecommerce Rest API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="indiekaj@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Django admin
    path("django-admin/", admin.site.urls),

    # React Admin SPA
    re_path(r"^admin/(?!static/|media/|assets/).*", react_admin_view),
    path("admin/", react_admin_view),

    # Django apps
    path("", include("ecommerce.urls")),
    path("", include("appcontent.urls")),
    path("accounts/", include("accounts.urls")),
    path("blogs/", include("blogs.urls")),
    path("payment/", include("payments.urls")),

    # API endpoints
    path("api/ecommerce/", include("ecommerce.api.urls")),
    path("api/analytics/", include("ecommerce.api.analytics.urls")),
    path("api/accounts/", include("accounts.api.urls")),
    path("api/", include("ecommerce.api.orders.urls")),
    path("api/blogs/", include("blogs.api.urls")),
    path("api/payments/", include("payments.api.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API Docs
    path("api/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

# Custom 404
handler404 = "accounts.views.error_404_view"


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static('/admin/', document_root=os.path.join(settings.BASE_DIR, 'dist'))
else:
    # In production, serve static and media files through Django (not recommended for high traffic sites)
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^admin/static/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.BASE_DIR, 'dist')}),
    ]