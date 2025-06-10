from django.urls import path
from .views import OrderAnalyticsView, SalesMetricsView, ProductAnalyticsView, CategoryAnalyticsView, DashboardSummaryView


urlpatterns = [
    path('orders/', OrderAnalyticsView.as_view(), name='order-analytics'),
    path('sales/', SalesMetricsView.as_view(), name='sales-metrics'),
    path('products/', ProductAnalyticsView.as_view(), name='product-analytics'),
    path('categories/', CategoryAnalyticsView.as_view(), name='category-analytics'),
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard-summary'),
]