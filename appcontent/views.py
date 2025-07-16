from django.shortcuts import render
from ecommerce.views.services import CommonService, ProductService
from appcontent.models import Faq
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Sum, Count, Avg, Q, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, ExtractHour
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from ecommerce.models import (
    Order, OrderItem, Product,
    Cart,WishlistItem,
)
from accounts.models import CustomUser
from payments.models import Transaction

class ComprehensiveDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        period = request.query_params.get('period', '30')  # Default 30 days
        
        try:
            days = int(period)
        except ValueError:
            days = 30
            
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Previous period for comparison
        prev_end_date = start_date
        prev_start_date = prev_end_date - timedelta(days=days)
        
        # 1. REVENUE METRICS
        revenue_metrics = self.get_revenue_metrics(start_date, end_date, prev_start_date, prev_end_date)
        
        # 2. ORDER METRICS
        order_metrics = self.get_order_metrics(start_date, end_date, prev_start_date, prev_end_date)
        
        # 3. CUSTOMER METRICS
        customer_metrics = self.get_customer_metrics(start_date, end_date)
        
        # 4. PRODUCT METRICS
        product_metrics = self.get_product_metrics(start_date, end_date)
        
        # 5. REAL-TIME METRICS
        realtime_metrics = self.get_realtime_metrics()
        
        # 6. CHARTS DATA
        charts_data = self.get_charts_data(start_date, end_date)
        
        # 7. GEOGRAPHIC DATA
        geographic_data = self.get_geographic_data(start_date, end_date)
        
        # 8. PAYMENT METRICS
        payment_metrics = self.get_payment_metrics(start_date, end_date)
        
        return Response({
            'period': {
                'days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'revenue': revenue_metrics,
            'orders': order_metrics,
            'customers': customer_metrics,
            'products': product_metrics,
            'realtime': realtime_metrics,
            'charts': charts_data,
            'geographic': geographic_data,
            'payments': payment_metrics
        })
    
    def get_revenue_metrics(self, start_date, end_date, prev_start_date, prev_end_date):
        # Current period revenue - separate queries for different aggregations
        current_orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            payment_status='Paid'
        )
        
        # Get total revenue and count
        current_revenue_total = current_orders.aggregate(
            total=Sum('total'),
            count=Count('id')
        )
        
        # Get average order value separately
        current_revenue_avg = current_orders.aggregate(
            avg=Avg('total')
        )
        
        # Previous period revenue
        prev_revenue = Order.objects.filter(
            created_at__gte=prev_start_date,
            created_at__lte=prev_end_date,
            payment_status='Paid'
        ).aggregate(total=Sum('total'))
        
        # Calculate growth
        current_total = current_revenue_total['total'] or Decimal('0')
        prev_total = prev_revenue['total'] or Decimal('0')
        growth = self.calculate_growth(current_total, prev_total)
        
        # Revenue by category
        revenue_by_category = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__payment_status='Paid'
        ).values(
            'product__category__category_name',
            'product__category__parent_category__parent_name'
        ).annotate(
            revenue=Sum('subtotal'),
            quantity=Sum('quantity')
        ).order_by('-revenue')[:10]
        
        # Revenue by brand
        revenue_by_brand = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__payment_status='Paid'
        ).values('product__brand__brand_title').annotate(
            revenue=Sum('subtotal'),
            quantity=Sum('quantity')
        ).order_by('-revenue')[:10]
        
        return {
            'total': float(current_total),
            'order_count': current_revenue_total['count'] or 0,
            'average_order_value': float(current_revenue_avg['avg'] or 0),
            'growth': growth,
            'by_category': list(revenue_by_category),
            'by_brand': list(revenue_by_brand)
        }
    
    def get_order_metrics(self, start_date, end_date, prev_start_date, prev_end_date):
        # Current period orders
        current_orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Order status breakdown
        status_breakdown = current_orders.values('status').annotate(
            count=Count('id'),
            revenue=Sum('total')
        ).order_by('status')
        
        # Payment status breakdown
        payment_breakdown = current_orders.values('payment_status').annotate(
            count=Count('id'),
            revenue=Sum('total')
        ).order_by('payment_status')
        
        # Orders comparison
        current_count = current_orders.count()
        prev_count = Order.objects.filter(
            created_at__gte=prev_start_date,
            created_at__lte=prev_end_date
        ).count()
        
        # Fulfillment rate
        fulfilled = current_orders.filter(status='Delivered').count()
        fulfillment_rate = (fulfilled / current_count * 100) if current_count > 0 else 0
        
        # Average processing time
        delivered_orders = current_orders.filter(
            status='Delivered',
            paid_at__isnull=False
        ).annotate(
            processing_days=ExpressionWrapper(
                F('updated_at') - F('paid_at'),
                output_field=DecimalField()
            )
        )
        
        avg_processing_time = delivered_orders.aggregate(
            avg_days=Avg('processing_days')
        )['avg_days']
        
        return {
            'total': current_count,
            'growth': self.calculate_growth(current_count, prev_count),
            'status_breakdown': list(status_breakdown),
            'payment_breakdown': list(payment_breakdown),
            'fulfillment_rate': round(fulfillment_rate, 2),
            'avg_processing_days': float(avg_processing_time.days) if avg_processing_time else 0,
            'pending': current_orders.filter(status='Pending').count(),
            'processing': current_orders.filter(status='Processing').count(),
            'shipped': current_orders.filter(status='Shipped').count(),
            'delivered': fulfilled,
            'cancelled': current_orders.filter(status='Cancelled').count()
        }
    
    def get_customer_metrics(self, start_date, end_date):
        # Total customers
        total_customers = CustomUser.objects.filter(role='Customer').count()
        
        # New customers in period
        new_customers = CustomUser.objects.filter(
            role='Customer',
            date_joined__gte=start_date,
            date_joined__lte=end_date
        ).count()
        
        # Returning customers
        returning_customers = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).values('user').annotate(
            order_count=Count('id')
        ).filter(order_count__gt=1).count()
        
        # Customer lifetime value
        customer_ltv = Order.objects.filter(
            payment_status='Paid'
        ).values('user__email', 'user__first_name', 'user__last_name').annotate(
            total_spent=Sum('total'),
            order_count=Count('id'),
            avg_order=Avg('total')
        ).order_by('-total_spent')[:10]
        
        # Customer segments
        segments = {
            'new': CustomUser.objects.filter(
                role='Customer',
                date_joined__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'active': Order.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=90)
            ).values('user').distinct().count(),
            'at_risk': Order.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=180),
                created_at__lt=timezone.now() - timedelta(days=90)
            ).values('user').distinct().count()
        }
        
        return {
            'total': total_customers,
            'new_this_period': new_customers,
            'returning': returning_customers,
            'retention_rate': round((returning_customers / total_customers * 100) if total_customers > 0 else 0, 2),
            'top_customers': list(customer_ltv),
            'segments': segments
        }
    
    def get_product_metrics(self, start_date, end_date):
        # Best selling products
        best_sellers = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__payment_status='Paid'
        ).values(
            'product__id',
            'product__title',
            'product__price',
            'product__prod_img'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('subtotal'),
            order_count=Count('order', distinct=True)
        ).order_by('-quantity_sold')[:10]
        
        # Low stock products
        low_stock = Product.objects.filter(
            quantity__lte=10,
            quantity__gt=0
        ).values('id', 'title', 'quantity', 'price')[:10]
        
        # Out of stock
        out_of_stock = Product.objects.filter(quantity=0).count()
        
        # Product performance by category
        category_performance = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__payment_status='Paid'
        ).values(
            'product__category__category_name'
        ).annotate(
            products_sold=Count('product', distinct=True),
            quantity_sold=Sum('quantity'),
            revenue=Sum('subtotal')
        ).order_by('-revenue')
        
        # Product views to purchase conversion
        total_products = Product.objects.count()
        products_with_sales = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date
        ).values('product').distinct().count()
        
        return {
            'best_sellers': list(best_sellers),
            'low_stock': list(low_stock),
            'out_of_stock_count': out_of_stock,
            'total_products': total_products,
            'products_sold': products_with_sales,
            'category_performance': list(category_performance)
        }
    
    def get_realtime_metrics(self):
        today = timezone.now().date()
        current_hour = timezone.now().hour
        
        # Today's metrics
        today_orders = Order.objects.filter(created_at__date=today)
        today_revenue = today_orders.filter(payment_status='Paid').aggregate(
            total=Sum('total')
        )['total'] or Decimal('0')
        
        # Active carts
        active_carts = Cart.objects.filter(
            updated_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Cart abandonment
        abandoned_carts = Cart.objects.filter(
            updated_at__lt=timezone.now() - timedelta(hours=24),
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Online visitors (you might need to implement visitor tracking)
        # For now, we'll use active carts as a proxy
        
        # Wishlist items
        wishlist_items = WishlistItem.objects.filter(
            added_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return {
            'today_orders': today_orders.count(),
            'today_revenue': float(today_revenue),
            'active_carts': active_carts,
            'abandoned_carts': abandoned_carts,
            'current_hour_orders': today_orders.filter(created_at__hour=current_hour).count(),
            'wishlist_items': wishlist_items
        }
    
    def get_charts_data(self, start_date, end_date):
        # Daily revenue chart
        daily_revenue = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            payment_status='Paid'
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            revenue=Sum('total'),
            orders=Count('id')
        ).order_by('date')
        
        # Hourly distribution
        hourly_distribution = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        # Weekly comparison
        weekly_data = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            payment_status='Paid'
        ).annotate(
            week=TruncWeek('created_at')
        ).values('week').annotate(
            revenue=Sum('total'),
            orders=Count('id')
        ).order_by('week')
        
        # Payment methods distribution
        payment_methods = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            payment_status='Paid'
        ).values('payment_method').annotate(
            count=Count('id'),
            revenue=Sum('total')
        ).order_by('-count')
        
        return {
            'daily_revenue': list(daily_revenue),
            'hourly_distribution': list(hourly_distribution),
            'weekly_comparison': list(weekly_data),
            'payment_methods': list(payment_methods)
        }
    
    def get_geographic_data(self, start_date, end_date):
        # Orders by city
        geographic_distribution = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            shipping_address__isnull=False
        ).values(
            'shipping_address__city',
            'shipping_address__county'
        ).annotate(
            orders=Count('id'),
            revenue=Sum('total'),
            customers=Count('user', distinct=True)
        ).order_by('-orders')[:20]
        
        return {
            'distribution': list(geographic_distribution)
        }
    
    def get_payment_metrics(self, start_date, end_date):
        # Transaction metrics
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Success rate
        total_transactions = transactions.count()
        successful = transactions.filter(status='Completed').count()
        success_rate = (successful / total_transactions * 100) if total_transactions > 0 else 0
        
        # Payment methods breakdown
        payment_breakdown = transactions.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount'),
            avg=Avg('amount')
        ).order_by('-count')
        
        # Failed transactions
        failed_transactions = transactions.filter(
            Q(status='Failed') | Q(status='Cancelled')
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return {
            'total_transactions': total_transactions,
            'successful_transactions': successful,
            'success_rate': round(success_rate, 2),
            'payment_methods': list(payment_breakdown),
            'failed': failed_transactions
        }
    
    def calculate_growth(self, current, previous):
        """Calculate percentage growth"""
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous * 100), 2)

def home(request):
    """
    Render home page with latest products and categories.
    """
    context = {
        'latest_products': ProductService.get_latest_products(),
        'featured_products' : ProductService.get_featured_products(),
        'categories': ProductService.get_featured_categories(),
        'path': 'home',
        **CommonService.get_common_context(request)
    }
    return render(request, 'home.html', context)

def about(request):
    """
    Render about page.
    """
    context = {
        'path': 'about',
        **CommonService.get_common_context(request)
    }
    return render(request, 'about.html', context)

def faq(request):
    """
    Render FAQ page.
    """
    faqs = Faq.objects.all()
    context = {
        'path': 'faq',
        'faqs': faqs,
        **CommonService.get_common_context(request)
    }
    return render(request, 'faq.html', context)
