from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import AllowAny
from django.db import models
# from django_filters.rest_framework import DjangoFilterBackend
from appcontent.utils import IsAdminUserOrReadOnly
from payments.api.serializers import TransactionSerializer
from payments.models import Transaction

class TransactionViewSet(viewsets.ViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]  # Change to IsAuthenticated for user-specific actions
    # permission_classes = [IsAdminUserOrReadOnly]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'user', 'order', 'timestamp', 'transaction_date']
    search_fields = ['receipt_number', 'transaction_id', 'description', 'phone_number']
    ordering_fields = ['timestamp', 'transaction_date', 'amount']
    ordering = ['-timestamp']  # Default ordering

    def list(self, request):
        queryset = self.queryset.all()
        
            
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
        
    '''def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset'''

    def retrieve(self, request, pk=None):
        try:
            transaction = self.queryset.get(pk=pk)
            serializer = self.serializer_class(transaction)
            return Response(serializer.data)
        except Transaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
            
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # Ensure the transaction is associated with the current user if not specified
            if not request.data.get('user') and request.user.is_authenticated:
                serializer.save(user=request.user)
            else:
                serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, pk=None):
        try:
            transaction = self.queryset.get(pk=pk)
            serializer = self.serializer_class(transaction, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Transaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
            
    def partial_update(self, request, pk=None):
        try:
            transaction = self.queryset.get(pk=pk)
            serializer = self.serializer_class(transaction, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Transaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
            
    def destroy(self, request, pk=None):
        try:
            transaction = self.queryset.get(pk=pk)
            transaction.delete()
            return Response({"detail": "Transaction deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Additional useful actions tailored to your Transaction model
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transactions (last 7 days)"""
        week_ago = timezone.now() - timedelta(days=7)
        recent_transactions = self.queryset.filter(timestamp__gte=week_ago).order_by('-timestamp')
        '''page = self.paginate_queryset(recent_transactions)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)'''
        serializer = self.serializer_class(recent_transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def payment_methods(self, request):
        """Group transactions by payment method with counts and totals"""
        method_stats = self.queryset.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('payment_method')
        return Response(method_stats)
    
    @action(detail=False, methods=['get'])
    def status_summary(self, request):
        """Group transactions by status with counts and totals"""
        status_stats = self.queryset.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('status')
        return Response(status_stats)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update transaction status with notes"""
        try:
            transaction = self.queryset.get(pk=pk)
            new_status = request.data.get('status')
            notes = request.data.get('notes')
            
            if not new_status:
                return Response({"detail": "Status is required."}, status=status.HTTP_400_BAD_REQUEST)
                
            transaction.status = new_status
            
            if notes:
                # Append to existing notes or create new ones
                if transaction.notes:
                    transaction.notes += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
                else:
                    transaction.notes = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
            
            transaction.save()
            serializer = self.serializer_class(transaction)
            return Response(serializer.data)
        except Transaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def my_transactions(self, request):
        """Get current user's transactions"""
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
            
        user_transactions = self.queryset.filter(user=request.user).order_by('-timestamp')
        page = self.paginate_queryset(user_transactions)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(user_transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_order(self, request):
        """Get transactions for a specific order"""
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response({"detail": "Order ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        order_transactions = self.queryset.filter(order_id=order_id).order_by('-timestamp')
        serializer = self.serializer_class(order_transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """Get transactions within a date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        use_transaction_date = request.query_params.get('use_transaction_date', 'false').lower() == 'true'
        
        if not start_date or not end_date:
            return Response(
                {"detail": "Both start_date and end_date are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Choose which date field to filter on
            date_field = 'transaction_date' if use_transaction_date else 'timestamp'
            
            filter_kwargs = {
                f'{date_field}__gte': start_date,
                f'{date_field}__lte': end_date
            }
            
            transactions = self.queryset.filter(**filter_kwargs).order_by(f'-{date_field}')
            
            page = self.paginate_queryset(transactions)
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.serializer_class(transactions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def phone_lookup(self, request):
        """Look up transactions by phone number"""
        phone = request.query_params.get('phone')
        if not phone:
            return Response({"detail": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Normalize phone number for flexible matching
        phone = phone.replace(' ', '').replace('-', '')
        transactions = self.queryset.filter(phone_number__icontains=phone).order_by('-timestamp')
        
        serializer = self.serializer_class(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get transaction statistics"""
        # Default to last 30 days if not specified
        days = int(request.query_params.get('days', 240))
        date_from = timezone.now() - timedelta(days=days)
        
        # Basic stats
        total_count = self.queryset.filter(timestamp__gte=date_from).count()
        total_amount = self.queryset.filter(timestamp__gte=date_from).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Status breakdown
        status_breakdown = self.queryset.filter(timestamp__gte=date_from).values('status').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Payment method breakdown
        payment_breakdown = self.queryset.filter(timestamp__gte=date_from).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Daily transaction count for timeline
        daily_counts = self.queryset.filter(timestamp__gte=date_from) \
            .extra(select={'day': "DATE(timestamp)"}) \
            .values('day') \
            .annotate(count=Count('id'), total=Sum('amount')) \
            .order_by('day')
        
        return Response({
            'total_transactions': total_count,
            'total_amount': total_amount,
            'status_breakdown': status_breakdown,
            'payment_breakdown': payment_breakdown,
            'daily_summary': daily_counts
        })