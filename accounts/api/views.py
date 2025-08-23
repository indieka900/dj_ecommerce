from rest_framework import status
from rest_framework.response import Response
from accounts.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from ..signals import send_otp_email
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import (
    PasswordChangeSerializer, PasswordResetConfirmSerializer, PasswordResetSerializer, RegistrationSerializer, LoginSerializer,
    TokenSerializer, UserProfileUpdateSerializer, VerifyOTPSerializer, AddAdminSerializer, CustomerCreateUpdateSerializer,
    CustomerOrderSerializer, CustomerListSerializer, CustomerDetailSerializer, CustomerStatsOverviewSerializer
)
import django_filters

class UserManagementViewSet(ViewSet):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully.",
                "user": UserProfileUpdateSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='all-users', permission_classes=[IsAdminUser])
    def all_users(self, request):
        """Get all users."""
        users = self.queryset.all()
        serializer = UserProfileUpdateSerializer(users, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='login')
    def login_user(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            # send_otp_email(user)
            return Response({
                'refresh': str(refresh),
                'access': str(access),
                "user": UserProfileUpdateSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        token_data = {
            'refresh': str(refresh),
            'access': str(access),
            'user_role': user.role,
        }
        token_serializer = TokenSerializer(token_data)

        return Response(token_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'put'], url_path='profile', permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        # Determine which user's profile to update
        target_user_id = request.query_params.get('user_id')
        is_admin = request.user.role == 'Administrator'
        
        if target_user_id and is_admin:
            try:
                target_user = CustomUser.objects.get(id=target_user_id)
            except CustomUser.DoesNotExist:
                return Response({"error": f"User {target_user_id} not found."}, 
                            status=status.HTTP_404_NOT_FOUND)
        elif target_user_id and not is_admin:
            return Response(
                {"error": "You don't have permission to update other users' profiles."},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            target_user = request.user
        
        if request.method == 'GET':
            serializer = UserProfileUpdateSerializer(
                target_user, 
                context={'request': request}
            )
            return Response(serializer.data)

        elif request.method == 'PUT' or request.method == 'PATCH':
            # Handle the profile update
            serializer = UserProfileUpdateSerializer(
                target_user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "Profile updated successfully.",
                    "user": serializer.data
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='password-reset')
    def password_reset(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password reset email sent'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Password reset email not sent'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='password-reset-confirm')
    def password_reset_confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password has been reset'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """Change user's password."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='add-admin', permission_classes=[IsAuthenticated])
    def add_admin(self, request):
        """Allow a superuser to add a new administrator."""
        if not request.user.is_superuser:
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddAdminSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Administrator added successfully.",
                "user": UserProfileUpdateSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='change-role', permission_classes=[IsAuthenticated])
    def change_role(self, request):
        """Change user's role.
        
        Only administrators are allowed to change roles.
        """
        # Check if the requesting user is an administrator
        if not request.user.is_superuser:
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        user_id = request.data.get('user_id')
        new_role = request.data.get('new_role')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": f"User {user_id} not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # If new_role is provided, use it directly
        if new_role:
            if new_role not in ['Customer', 'Administrator']:
                return Response(
                    {"error": "Invalid role. Must be 'Customer' or 'Administrator'."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.role = new_role
            
        else:
            
            if user.role == 'Administrator':
                user.role = 'Customer'
            else:
                user.role = 'Administrator'
        
        if user.role == 'Administrator':
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False
            
        user.save()
        
        return Response({
            "message": "User role changed successfully.", 
            "user_id": user_id,
            "new_role": user.role
        }, status=status.HTTP_200_OK)
        

class CustomerFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        field_name='is_active',
        choices=[
            ('Active', True),
            ('Inactive', False),
        ],
        method='filter_status'
    )
    tier = django_filters.ChoiceFilter(
        choices=[
            ('Bronze', 'Bronze'),
            ('Silver', 'Silver'),
            ('Gold', 'Gold'),
            ('Platinum', 'Platinum'),
        ],
        method='filter_tier'
    )
    date_joined_after = django_filters.DateFilter(field_name='date_joined', lookup_expr='gte')
    date_joined_before = django_filters.DateFilter(field_name='date_joined', lookup_expr='lte')
    total_spent_min = django_filters.NumberFilter(method='filter_total_spent_min')
    total_spent_max = django_filters.NumberFilter(method='filter_total_spent_max')
    is_vip = django_filters.BooleanFilter(method='filter_vip')

    class Meta:
        model = CustomUser
        fields = ['role']

    def filter_status(self, queryset, name, value):
        return queryset.filter(is_active=value)

    def filter_tier(self, queryset, name, value):
        # This is a simplified tier filter - you might want to use raw SQL for better performance
        tier_ranges = {
            'Bronze': (0, 499.99),
            'Silver': (500, 1999.99),
            'Gold': (2000, 4999.99),
            'Platinum': (5000, float('inf'))
        }
        min_val, max_val = tier_ranges.get(value, (0, float('inf')))
        
        # Get users with total spent in range
        user_ids = []
        for user in queryset:
            total_spent = user.orders.filter(payment_status='Paid').aggregate(
                total=Sum('total'))['total'] or 0
            if min_val <= total_spent <= max_val:
                user_ids.append(user.id)
        
        return queryset.filter(id__in=user_ids)

    def filter_total_spent_min(self, queryset, name, value):
        user_ids = []
        for user in queryset:
            total_spent = user.orders.filter(payment_status='Paid').aggregate(
                total=Sum('total'))['total'] or 0
            if total_spent >= value:
                user_ids.append(user.id)
        return queryset.filter(id__in=user_ids)

    def filter_total_spent_max(self, queryset, name, value):
        user_ids = []
        for user in queryset:
            total_spent = user.orders.filter(payment_status='Paid').aggregate(
                total=Sum('total'))['total'] or 0
            if total_spent <= value:
                user_ids.append(user.id)
        return queryset.filter(id__in=user_ids)

    def filter_vip(self, queryset, name, value):
        user_ids = []
        for user in queryset:
            total_spent = user.orders.filter(payment_status='Paid').aggregate(
                total=Sum('total'))['total'] or 0
            is_vip = total_spent >= 5000
            if is_vip == value:
                user_ids.append(user.id)
        return queryset.filter(id__in=user_ids)

class CustomerViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CustomerFilter
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['date_joined', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    def get_queryset(self):
        return CustomUser.objects.filter().prefetch_related('orders')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CustomerCreateUpdateSerializer
        elif self.action == 'retrieve':
            return CustomerDetailSerializer
        return CustomerListSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get customer statistics overview"""
        now = timezone.now()
        last_month = now - timedelta(days=30)
        
        customers = CustomUser.objects.filter()
        
        # Basic stats
        total_customers = customers.count()
        active_customers = customers.filter(is_active=True).count()
        inactive_customers = customers.filter(is_active=False).count()
        new_customers_this_month = customers.filter(date_joined__gte=last_month).count()
        
        # VIP customers (total spent >= 5000)
        vip_customers = 0
        total_revenue = 0
        
        for customer in customers:
            customer_spent = customer.orders.filter(payment_status='Paid').aggregate(
                total=Sum('total'))['total'] or 0
            total_revenue += customer_spent
            if customer_spent >= 5000:
                vip_customers += 1
        
        stats_data = {
            'total_customers': total_customers,
            'active_customers': active_customers,
            'inactive_customers': inactive_customers,
            'vip_customers': vip_customers,
            'total_revenue': total_revenue,
            'new_customers_this_month': new_customers_this_month,
        }
        
        serializer = CustomerStatsOverviewSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """Get customer's order history"""
        customer = self.get_object()
        orders = customer.orders.all()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        payment_status_filter = request.query_params.get('payment_status')
        if payment_status_filter:
            orders = orders.filter(payment_status=payment_status_filter)
        
        date_from = request.query_params.get('date_from')
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
        
        serializer = CustomerOrderSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate customer"""
        customer = self.get_object()
        customer.is_active = True
        customer.save()
        return Response({'status': 'Customer activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate customer"""
        customer = self.get_object()
        customer.is_active = False
        customer.save()
        return Response({'status': 'Customer deactivated'})
    
    # @action(detail=True, methods=['post'])
    # def delete(self, request, pk=None):
    #     """Delete customer"""
    #     customer = self.get_object()
    #     customer.delete()
    #     return Response({'status': 'Customer Deleted'})

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on customers"""
        action_type = request.data.get('action')
        customer_ids = request.data.get('customer_ids', [])
        
        if not action_type or not customer_ids:
            return Response(
                {'error': 'Action and customer_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        customers = CustomUser.objects.filter(id__in=customer_ids, role='Customer')
        
        if action_type == 'activate':
            customers.update(is_active=True)
            return Response({'status': f'{customers.count()} customers activated'})
        
        elif action_type == 'deactivate':
            customers.update(is_active=False)
            return Response({'status': f'{customers.count()} customers deactivated'})
        
        elif action_type == 'delete':
            count = customers.count()
            customers.delete()
            return Response({'status': f'{count} customers deleted'})
        
        else:
            return Response(
                {'error': 'Invalid action type'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export customers to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customers.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Email', 'First Name', 'Last Name', 'Phone', 
            'Status', 'Join Date', 'Total Orders', 'Total Spent', 'Tier'
        ])
        
        customers = self.filter_queryset(self.get_queryset())
        for customer in customers:
            total_orders = customer.orders.filter(payment_status='Paid').count()
            total_spent = customer.orders.filter(payment_status='Paid').aggregate(
                total=Sum('total'))['total'] or 0
            
            # Calculate tier
            if total_spent >= 5000:
                tier = 'Platinum'
            elif total_spent >= 2000:
                tier = 'Gold'
            elif total_spent >= 500:
                tier = 'Silver'
            else:
                tier = 'Bronze'
            
            writer.writerow([
                customer.id,
                customer.email,
                customer.first_name or '',
                customer.last_name or '',
                customer.phone_number,
                'Active' if customer.is_active else 'Inactive',
                customer.date_joined.strftime('%Y-%m-%d'),
                total_orders,
                total_spent,
                tier
            ])
        
        return response

    @action(detail=True, methods=['get'])
    def activity_log(self, request, pk=None):
        """Get customer activity log"""
        customer = self.get_object()
        
        # Combine different activities
        activities = []
        
        # Order activities
        for order in customer.orders.all()[:20]:  # Last 20 orders
            activities.append({
                'id': f"order_{order.id}",
                'type': 'order',
                'action': 'Order Placed',
                'description': f'Order #{order.order_number} placed',
                'date': order.created_at,
                'details': {
                    'order_number': order.order_number,
                    'total': str(order.total),
                    'status': order.status
                }
            })
            
            if order.paid_at:
                activities.append({
                    'id': f"payment_{order.id}",
                    'type': 'payment',
                    'action': 'Payment Received',
                    'description': f'Payment received for order #{order.order_number}',
                    'date': order.paid_at,
                    'details': {
                        'order_number': order.order_number,
                        'amount': str(order.total),
                        'payment_method': order.payment_method
                    }
                })
        
        # Account activities
        activities.append({
            'id': f"registration_{customer.id}",
            'type': 'account',
            'action': 'Account Created',
            'description': 'Customer account created',
            'date': customer.date_joined,
            'details': {}
        })
        
        # Sort by date (newest first)
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        return Response(activities[:50]) 