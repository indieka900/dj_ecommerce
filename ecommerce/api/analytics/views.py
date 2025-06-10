from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from ecommerce.models import Order, OrderItem, Product, Category, ParentCategory
from accounts.models import CustomUser as User
from .serializers import (
    OrderAnalyticsSerializer, 
    SalesMetricsSerializer,
    ProductAnalyticsSerializer,
    CategoryAnalyticsSerializer
)

class OrderAnalyticsView(APIView):
    """
    Get comprehensive order analytics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            # Get date filters from query params
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            # Set default date range if not provided
            if not start_date:
                start_date = timezone.now() - timedelta(days=30)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                
            if not end_date:
                end_date = timezone.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Base queryset
            orders = Order.objects.all()
            
            # Date-based calculations
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            last_month_start = (month_start - timedelta(days=1)).replace(day=1)
            last_month_end = month_start - timedelta(days=1)
            
            # Total orders by status
            total_orders = orders.count()
            status_counts = orders.values('status').annotate(count=Count('id'))
            status_dict = {item['status']: item['count'] for item in status_counts}
            
            # Time-based order counts
            orders_today = orders.filter(created_at__date=today).count()
            orders_this_week = orders.filter(created_at__date__gte=week_start).count()
            orders_this_month = orders.filter(created_at__date__gte=month_start).count()
            orders_last_month = orders.filter(
                created_at__date__gte=last_month_start,
                created_at__date__lte=last_month_end
            ).count()
            
            # Growth calculations
            last_week_orders = orders.filter(
                created_at__date__gte=week_start - timedelta(days=7),
                created_at__date__lt=week_start
            ).count()
            
            weekly_growth_rate = (
                ((orders_this_week - last_week_orders) / last_week_orders * 100)
                if last_week_orders > 0 else 0
            )
            
            monthly_growth_rate = (
                ((orders_this_month - orders_last_month) / orders_last_month * 100)
                if orders_last_month > 0 else 0
            )
            
            # Average order value
            avg_order_value = orders.aggregate(
                avg_total=Avg('total')
            )['avg_total'] or Decimal('0.00')
            
            analytics_data = {
                'total_orders': total_orders,
                'pending_orders': status_dict.get('Pending', 0),
                'processing_orders': status_dict.get('Processing', 0),
                'shipped_orders': status_dict.get('Shipped', 0),
                'delivered_orders': status_dict.get('Delivered', 0),
                'cancelled_orders': status_dict.get('Cancelled', 0),
                'refunded_orders': status_dict.get('Refunded', 0),
                'orders_today': orders_today,
                'orders_this_week': orders_this_week,
                'orders_this_month': orders_this_month,
                'orders_last_month': orders_last_month,
                'weekly_growth_rate': round(weekly_growth_rate, 2),
                'monthly_growth_rate': round(monthly_growth_rate, 2),
                'average_order_value': round(avg_order_value, 2),
            }
            
            serializer = OrderAnalyticsSerializer(data=analytics_data)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching order analytics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SalesMetricsView(APIView):
    """
    Get comprehensive sales metrics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            # Date calculations
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            last_month_start = (month_start - timedelta(days=1)).replace(day=1)
            last_month_end = month_start - timedelta(days=1)
            
            # Revenue calculations
            paid_orders = Order.objects.filter(payment_status='Paid')
            
            total_revenue = paid_orders.aggregate(
                total=Sum('total')
            )['total'] or Decimal('0.00')
            
            revenue_today = paid_orders.filter(
                created_at__date=today
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            revenue_this_week = paid_orders.filter(
                created_at__date__gte=week_start
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            revenue_this_month = paid_orders.filter(
                created_at__date__gte=month_start
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            revenue_last_month = paid_orders.filter(
                created_at__date__gte=last_month_start,
                created_at__date__lte=last_month_end
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            # Growth calculations
            last_week_revenue = paid_orders.filter(
                created_at__date__gte=week_start - timedelta(days=7),
                created_at__date__lt=week_start
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            weekly_revenue_growth = (
                float((revenue_this_week - last_week_revenue) / last_week_revenue * 100)
                if last_week_revenue > 0 else 0
            )
            
            monthly_revenue_growth = (
                float((revenue_this_month - revenue_last_month) / revenue_last_month * 100)
                if revenue_last_month > 0 else 0
            )
            
            # Product metrics
            total_products_sold = OrderItem.objects.filter(
                order__payment_status='Paid'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            # Top selling products
            top_products = OrderItem.objects.filter(
                order__payment_status='Paid'
            ).values('product__title').annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum('subtotal')
            ).order_by('-total_sold')[:10]
            
            # Top categories
            top_categories = OrderItem.objects.filter(
                order__payment_status='Paid'
            ).values('product__category__category_name').annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum('subtotal')
            ).order_by('-total_revenue')[:10]
            
            # Customer metrics
            total_customers = User.objects.count()
            # new_customers_this_month = User.objects.filter(
            #     date_joined__date__gte=month_start
            # ).count()
            
            # Repeat customers (customers with more than 1 order)
            repeat_customers = User.objects.annotate(
                order_count=Count('orders')
            ).filter(order_count__gt=1).count()
            
            metrics_data = {
                'total_revenue': total_revenue,
                'revenue_today': revenue_today,
                'revenue_this_week': revenue_this_week,
                'revenue_this_month': revenue_this_month,
                'revenue_last_month': revenue_last_month,
                'weekly_revenue_growth': round(weekly_revenue_growth, 2),
                'monthly_revenue_growth': round(monthly_revenue_growth, 2),
                'total_products_sold': total_products_sold,
                'top_selling_products': list(top_products),
                'top_categories': list(top_categories),
                'total_customers': total_customers,
                # 'new_customers_this_month': new_customers_this_month,
                'repeat_customers': repeat_customers,
            }
            
            serializer = SalesMetricsSerializer(data=metrics_data)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching sales metrics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProductAnalyticsView(APIView):
    """
    Get product performance analytics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            # Get query parameters
            limit = int(request.query_params.get('limit', 20))
            category_id = request.query_params.get('category_id')
            
            # Base queryset for products with sales data
            products_query = Product.objects.annotate(
                total_sold=Sum('orderitem__quantity', filter=Q(orderitem__order__payment_status='Paid')),
                total_revenue=Sum('orderitem__subtotal', filter=Q(orderitem__order__payment_status='Paid')),
                avg_rating=Avg('reviews__rating')
            ).filter(total_sold__isnull=False)
            
            # Filter by category if provided
            if category_id:
                products_query = products_query.filter(category_id=category_id)
            
            # Order by total sold and limit results
            products = products_query.order_by('-total_sold')[:limit]
            
            analytics_data = []
            for product in products:
                analytics_data.append({
                    'product_id': product.id,
                    'product_name': product.title,
                    'total_sold': product.total_sold or 0,
                    'total_revenue': product.total_revenue or Decimal('0.00'),
                    'average_rating': round(product.avg_rating or 0, 2),
                    'stock_level': product.quantity,
                })
            
            serializer = ProductAnalyticsSerializer(data=analytics_data, many=True)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching product analytics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CategoryAnalyticsView(APIView):
    """
    Get category performance analytics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            # Get category performance data
            categories = Category.objects.annotate(
                total_products=Count('product'),
                total_sold=Sum('product__orderitem__quantity', 
                            filter=Q(product__orderitem__order__payment_status='Paid')),
                total_revenue=Sum('product__orderitem__subtotal', 
                                filter=Q(product__orderitem__order__payment_status='Paid'))
            ).filter(total_sold__isnull=False).order_by('-total_revenue')
            
            analytics_data = []
            for category in categories:
                analytics_data.append({
                    'category_name': category.category_name,
                    'total_products': category.total_products,
                    'total_sold': category.total_sold or 0,
                    'total_revenue': category.total_revenue or Decimal('0.00'),
                })
            
            serializer = CategoryAnalyticsSerializer(data=analytics_data, many=True)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching category analytics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardSummaryView(APIView):
    """
    Get dashboard summary with key metrics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            today = timezone.now().date()
            month_start = today.replace(day=1)
            
            # Quick summary metrics
            summary = {
                'total_orders': Order.objects.count(),
                'total_revenue': Order.objects.filter(
                    payment_status='Paid'
                ).aggregate(total=Sum('total'))['total'] or Decimal('0.00'),
                'orders_this_month': Order.objects.filter(
                    created_at__date__gte=month_start
                ).count(),
                'revenue_this_month': Order.objects.filter(
                    payment_status='Paid',
                    created_at__date__gte=month_start
                ).aggregate(total=Sum('total'))['total'] or Decimal('0.00'),
                'total_products': Product.objects.count(),
                'low_stock_products': Product.objects.filter(quantity__lt=10).count(),
                'total_customers': User.objects.count(),
                'pending_orders': Order.objects.filter(status='Pending').count(),
            }
            
            return Response(summary, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching dashboard summary: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

