from rest_framework import serializers
from ecommerce.models import (
    Brand, Category, Product, Review, Order, 
    OrderItem, Cart, CartItem, Wishlist, ProductImage, ProductVariant
)

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'brand_title', 'slug']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'category_name', 'slug', 'parent']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['product','image', 'alt_text']
        read_only_fields = ['product']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['size', 'stock', 'color', 'variant_price']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)  
    variants = ProductVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    brand_name = serializers.CharField(source='brand.brand_title', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'brand','brand_name', 'title', 'price', 'featured',
            'discount', 'quantity', 'description', 'keywords', 'created_at', 
            'updated_at', 'images', 'variants'
        ]
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'review', 'rating', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    # product = ProductSerializer(read_only=True)
    product_name = serializers.CharField(source='product.title', read_only=True)
    variant_name = serializers.CharField(source='variant.size', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product_name', 'variant_name', 'quantity', 'unit_price', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'total', 'shipping_address', 
            'transaction_id', 'payment_status', 'created_at', 'updated_at', 
            'items', 'total_items'
        ]

    def create(self, validated_data):
        order_items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())
    
class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, source='cartitem_set')

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at', 'updated_at']

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'products', 'created_at', 'updated_at']