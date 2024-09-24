from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserManagementViewSet

router = DefaultRouter()
router.register('user', UserManagementViewSet, basename='user-management')

urlpatterns = [
    path('', include(router.urls)),
]