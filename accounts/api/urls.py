from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserManagementViewSet, CustomerViewSet

router = DefaultRouter()
router.register('user', UserManagementViewSet, basename='user-management')
router.register('customers', CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls)),
]