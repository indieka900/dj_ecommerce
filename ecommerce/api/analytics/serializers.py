from rest_framework import serializers
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from django.utils import timezone

class OrderAnalyticsSerializer(serializers.Serializer):
    """Serializer for order analytics data"""
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    processing_orders = serializers.IntegerField()
    shipped_orders = serializers.IntegerField()
    delivered_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    refunded_orders = serializers.IntegerField()
    
    # Order trends
    orders_today = serializers.IntegerField()
    orders_this_week = serializers.IntegerField()
    orders_this_month = serializers.IntegerField()
    orders_last_month = serializers.IntegerField()
    
    # Growth metrics
    weekly_growth_rate = serializers.FloatField()
    monthly_growth_rate = serializers.FloatField()
    
    # Average order value
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)

class SalesMetricsSerializer(serializers.Serializer):
    """Serializer for sales metrics data"""
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    revenue_today = serializers.DecimalField(max_digits=15, decimal_places=2)
    revenue_this_week = serializers.DecimalField(max_digits=15, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    revenue_last_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Growth metrics
    weekly_revenue_growth = serializers.FloatField()
    monthly_revenue_growth = serializers.FloatField()
    
    # Product metrics
    total_products_sold = serializers.IntegerField()
    top_selling_products = serializers.ListField()
    top_categories = serializers.ListField()
    
    # Customer metrics
    total_customers = serializers.IntegerField()
    # new_customers_this_month = serializers.IntegerField()
    repeat_customers = serializers.IntegerField()

class ProductAnalyticsSerializer(serializers.Serializer):
    """Serializer for product analytics"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_rating = serializers.FloatField()
    stock_level = serializers.IntegerField()

class CategoryAnalyticsSerializer(serializers.Serializer):
    """Serializer for category analytics"""
    category_name = serializers.CharField()
    total_products = serializers.IntegerField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)