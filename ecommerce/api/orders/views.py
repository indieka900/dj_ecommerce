import django_filters
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Avg, Q, F
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from datetime import datetime, timedelta
from ecommerce.models import Order, OrderItem
from .serializers import OrderListSerializer, OrderDetailSerializer

User = get_user_model()


class OrderFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    min_total = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    max_total = django_filters.NumberFilter(field_name='total', lookup_expr='lte')
    user_email = django_filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    
    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'payment_method', 'user']

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrderFilter
    search_fields = ['order_number', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'total', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Order.objects.select_related('user', 'shipping_address', 'billing_address')
        
        if self.action == 'list':
            queryset = queryset.prefetch_related('items').annotate(
                items_count=Count('items')
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        return Response({'status': 'Order status updated'})
    
    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        """Update payment status"""
        order = self.get_object()
        new_payment_status = request.data.get('payment_status')
        
        if new_payment_status not in dict(Order.PAYMENT_STATUS_CHOICES):
            return Response(
                {'error': 'Invalid payment status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.payment_status = new_payment_status
        if new_payment_status == 'Paid' and not order.paid_at:
            order.paid_at = timezone.now()
        
        order.save()
        
        return Response({'status': 'Payment status updated'})
    
    @action(detail=True, methods=['post'])
    def add_tracking(self, request, pk=None):
        """Add tracking number to order"""
        order = self.get_object()
        tracking_number = request.data.get('tracking_number')
        
        if not tracking_number:
            return Response(
                {'error': 'Tracking number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.tracking_number = tracking_number
        if order.status == 'Processing':
            order.status = 'Shipped'
        order.save()
        
        return Response({
            'status': 'Tracking number added',
            'tracking_number': tracking_number
        })
    
    # @action(detail=False, methods=['get'])
    # def export_csv(self, request):
    #     """Export orders to CSV"""
    #     queryset = self.filter_queryset(self.get_queryset())
        
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        
    #     writer = csv.writer(response)
    #     writer.writerow([
    #         'Order Number', 'Date', 'Customer Name', 'Customer Email', 
    #         'Status', 'Payment Status', 'Total', 'Items Count',
    #         'Shipping Address', 'Phone'
    #     ])
        
    #     for order in queryset:
    #         customer_name = f"{order.shipping_address.first_name} {order.shipping_address.last_name}" if order.shipping_address else order.user.get_full_name()
    #         shipping_address = ""
    #         phone = ""
            
    #         if order.shipping_address:
    #             addr = order.shipping_address
    #             shipping_address = f"{addr.street_address}, {addr.city}, {addr.county} {addr.postal_code}"
    #             phone = addr.phone
            
    #         writer.writerow([
    #             order.order_number,
    #             order.created_at.strftime('%Y-%m-%d %H:%M'),
    #             customer_name,
    #             order.user.email,
    #             order.status,
    #             order.payment_status,
    #             order.total,
    #             order.items.count(),
    #             shipping_address,
    #             phone
    #         ])
        
    #     return response
    
    # @action(detail=False, methods=['get'])
    # def export_excel(self, request):
    #     """Export orders to Excel"""
    #     queryset = self.filter_queryset(self.get_queryset())
        
    #     wb = Workbook()
    #     ws = wb.active
    #     ws.title = "Orders"
        
    #     # Headers
    #     headers = [
    #         'Order Number', 'Date', 'Customer Name', 'Customer Email',
    #         'Status', 'Payment Status', 'Total', 'Items Count',
    #         'Shipping Address', 'Phone', 'Payment Method'
    #     ]
    #     ws.append(headers)
        
    #     for order in queryset:
    #         customer_name = f"{order.shipping_address.first_name} {order.shipping_address.last_name}" if order.shipping_address else order.user.get_full_name()
    #         shipping_address = ""
    #         phone = ""
            
    #         if order.shipping_address:
    #             addr = order.shipping_address
    #             shipping_address = f"{addr.street_address}, {addr.city}, {addr.county} {addr.postal_code}"
    #             phone = addr.phone
            
    #         ws.append([
    #             order.order_number,
    #             order.created_at.strftime('%Y-%m-%d %H:%M'),
    #             customer_name,
    #             order.user.email,
    #             order.status,
    #             order.payment_status,
    #             float(order.total),
    #             order.items.count(),
    #             shipping_address,
    #             phone,
    #             order.payment_method or 'N/A'
    #         ])
        
    #     # Save to BytesIO
    #     excel_file = BytesIO()
    #     wb.save(excel_file)
    #     excel_file.seek(0)
        
    #     response = HttpResponse(
    #         excel_file.getvalue(),
    #         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    #     )
    #     response['Content-Disposition'] = 'attachment; filename="orders_export.xlsx"'
        
    #     return response
    
    @action(detail=False, methods=['get'])
    def bulk_update_status(self, request):
        """Bulk update order status"""
        order_ids = request.query_params.getlist('ids[]')
        new_status = request.query_params.get('status')
        
        if not order_ids or not new_status:
            return Response(
                {'error': 'Order IDs and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = Order.objects.filter(id__in=order_ids).update(status=new_status)
        
        return Response({
            'status': 'Orders updated',
            'updated_count': updated
        })

class OrderAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset for the period
        orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        
        # Overall statistics
        total_orders = orders.count()
        total_revenue = orders.filter(payment_status='Paid').aggregate(
            total=Sum('total')
        )['total'] or 0
        
        avg_order_value = orders.filter(payment_status='Paid').aggregate(
            avg=Avg('total')
        )['avg'] or 0
        
        # Orders by status
        orders_by_status = orders.values('status').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('status')
        
        # Orders by payment status
        orders_by_payment_status = orders.values('payment_status').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('payment_status')
        
        # Daily revenue for the period
        daily_revenue = orders.filter(payment_status='Paid').annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            orders=Count('id'),
            revenue=Sum('total')
        ).order_by('date')
        
        # Top selling products
        top_products = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__payment_status='Paid'
        ).values('product_name').annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('subtotal')
        ).order_by('-quantity_sold')[:10]
        
        # Customer statistics
        top_customers = orders.filter(payment_status='Paid').values(
            'user__email', 'user__first_name', 'user__last_name'
        ).annotate(
            orders_count=Count('id'),
            total_spent=Sum('total')
        ).order_by('-total_spent')[:10]
        
        # Recent orders
        recent_orders = OrderListSerializer(
            orders.select_related('user').order_by('-created_at')[:10],
            many=True
        ).data
        
        return Response({
            'summary': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'average_order_value': float(avg_order_value),
                'period_days': days
            },
            'orders_by_status': list(orders_by_status),
            'orders_by_payment_status': list(orders_by_payment_status),
            'daily_revenue': list(daily_revenue),
            'top_products': list(top_products),
            'top_customers': list(top_customers),
            'recent_orders': recent_orders
        })

class OrderDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        today = timezone.now().date()
        
        # Today's stats
        today_orders = Order.objects.filter(created_at__date=today)
        today_revenue = today_orders.filter(payment_status='Paid').aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # This month's stats
        current_month_orders = Order.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        )
        month_revenue = current_month_orders.filter(payment_status='Paid').aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Pending orders
        pending_orders = Order.objects.filter(status='Pending').count()
        
        # Processing orders
        processing_orders = Order.objects.filter(status='Processing').count()
        
        # Failed payments
        failed_payments = Order.objects.filter(payment_status='Failed').count()
        
        # Conversion rate (paid orders / total orders)
        total_orders = Order.objects.count()
        paid_orders = Order.objects.filter(payment_status='Paid').count()
        conversion_rate = (paid_orders / total_orders * 100) if total_orders > 0 else 0
        
        return Response({
            'today': {
                'orders': today_orders.count(),
                'revenue': float(today_revenue)
            },
            'this_month': {
                'orders': current_month_orders.count(),
                'revenue': float(month_revenue)
            },
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'failed_payments': failed_payments,
            'conversion_rate': round(conversion_rate, 2)
        })

class RevenueAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        period = request.query_params.get('period', 'monthly')  # daily, monthly, yearly
        year = int(request.query_params.get('year', timezone.now().year))
        
        orders = Order.objects.filter(
            payment_status='Paid',
            created_at__year=year
        )
        
        if period == 'daily':
            month = int(request.query_params.get('month', timezone.now().month))
            orders = orders.filter(created_at__month=month)
            
            revenue_data = orders.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                revenue=Sum('total'),
                orders=Count('id'),
                avg_order_value=Avg('total')
            ).order_by('date')
            
        elif period == 'monthly':
            revenue_data = orders.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                revenue=Sum('total'),
                orders=Count('id'),
                avg_order_value=Avg('total')
            ).order_by('month')
            
        else:  # yearly
            orders = Order.objects.filter(payment_status='Paid')
            revenue_data = orders.annotate(
                year=TruncYear('created_at')
            ).values('year').annotate(
                revenue=Sum('total'),
                orders=Count('id'),
                avg_order_value=Avg('total')
            ).order_by('year')
        
        return Response({
            'period': period,
            'data': list(revenue_data)
        })
        
class CustomerOrderAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Get customer-specific analytics"""
        # Customer acquisition over time
        customer_acquisition = User.objects.filter(
            last_login__isnull=False
        ).annotate(
            month=TruncMonth('last_login')
        ).values('month').annotate(
            new_customers=Count('id')
        ).order_by('month')
        
        # Customer lifetime value
        customer_ltv = Order.objects.filter(
            payment_status='Paid'
        ).values('user').annotate(
            total_spent=Sum('total'),
            orders_count=Count('id'),
            avg_order_value=Avg('total')
        ).order_by('-total_spent')[:20]
        
        # Repeat customer rate
        customers_with_orders = Order.objects.values('user').distinct().count()
        repeat_customers = Order.objects.values('user').annotate(
            order_count=Count('id')
        ).filter(order_count__gt=1).count()
        
        repeat_rate = (repeat_customers / customers_with_orders * 100) if customers_with_orders > 0 else 0
        
        # Geographic distribution
        geographic_distribution = Order.objects.filter(
            shipping_address__isnull=False
        ).values('shipping_address__county').annotate(
            orders=Count('id'),
            revenue=Sum('total')
        ).order_by('-orders')[:10]
        
        return Response({
            'customer_acquisition': list(customer_acquisition),
            'top_customers': list(customer_ltv),
            'repeat_customer_rate': round(repeat_rate, 2),
            'geographic_distribution': list(geographic_distribution)
        })

class OrderSearchView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Advanced order search"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'results': []})
        
        # Search in multiple fields
        orders = Order.objects.filter(
            Q(order_number__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(shipping_address__first_name__icontains=query) |
            Q(shipping_address__last_name__icontains=query) |
            Q(shipping_address__phone__icontains=query) |
            Q(tracking_number__icontains=query)
        ).select_related('user', 'shipping_address')[:20]
        
        serializer = OrderListSerializer(orders, many=True)
        
        return Response({'results': serializer.data})