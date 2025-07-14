from rest_framework import serializers
from accounts.models import Address
from ecommerce.models import Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'street_address', 'apartment', 'city', 'county', 
            'postal_code', 'is_default', 'notes'
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(read_only=True)
    variant_info = serializers.JSONField(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant', 'quantity', 
            'unit_price', 'subtotal', 'product_name', 'variant_info'
        ]

class OrderListSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    items_count = serializers.IntegerField(read_only=True)
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_email', 'user_name',
            'customer_name', 'status', 'payment_status', 'total', 
            'created_at', 'items_count', 'payment_method'
        ]
    
    def get_user_name(self, obj : Order):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_customer_name(self, obj: Order):
        # Try to get name from shipping address first
        if obj.shipping_address:
            return f"{obj.shipping_address.first_name} {obj.shipping_address.last_name}".strip()
        # Fall back to user name
        return self.get_user_name(obj)

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order details"""
    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'tracking_number', 'notes']