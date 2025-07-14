from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet, OrderAnalyticsView, 
    OrderDashboardStatsView, RevenueAnalyticsView,
    CustomerOrderAnalyticsView, OrderSearchView
)

router = DefaultRouter()
router.register('orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/orders/', OrderAnalyticsView.as_view(), name='order-analytics'),
    path('analytics/dashboard-stats/', OrderDashboardStatsView.as_view(), name='dashboard-stats'),
    path('analytics/revenue/', RevenueAnalyticsView.as_view(), name='revenue-analytics'),
    path('analytics/customers/', CustomerOrderAnalyticsView.as_view(), name='customer-analytics'),
    path('orders/search/', OrderSearchView.as_view(), name='order-search'),
]