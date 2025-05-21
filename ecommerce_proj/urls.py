from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ecommerce.urls')),
    path('', include('appcontent.urls')),
    path('accounts/', include('accounts.urls')),
    path('blogs/', include('blogs.urls')),
    path('payment/', include('payments.urls')),
    path('api/ecommerce/', include('ecommerce.api.urls')),
    path('api/accounts/', include('accounts.api.urls')),
    path('api/blogs/', include('blogs.api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

handler404 = 'accounts.views.error_404_view'

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
