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
        
class BulkProductImageSerializer(serializers.Serializer):
    """Serializer for bulk image upload"""
    product = serializers.IntegerField()
    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=10,  # Limit to 10 images per request
        help_text="List of images to upload (max 10)"
    )
    alt_texts = serializers.ListField(
        child=serializers.CharField(max_length=255, required=False, allow_blank=True),
        required=False,
        help_text="Optional list of alt texts corresponding to each image"
    )

    def validate_product(self, value):
        """Validate that the product exists"""
        try:
            Product.objects.get(id=value)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product with the specified ID does not exist.")

    def validate(self, data):
        """Validate that alt_texts length matches images length if provided"""
        images = data.get('images', [])
        alt_texts = data.get('alt_texts', [])
        
        if alt_texts and len(alt_texts) != len(images):
            raise serializers.ValidationError(
                "Number of alt texts must match number of images if provided."
            )
        
        return data

    def create(self, validated_data):
        """Create multiple ProductImage instances"""
        product_id = validated_data['product']
        images = validated_data['images']
        alt_texts = validated_data.get('alt_texts', [])
        
        product = Product.objects.get(id=product_id)
        created_images = []
        
        for i, image in enumerate(images):
            alt_text = alt_texts[i] if i < len(alt_texts) else ""
            
            product_image = ProductImage.objects.create(
                product=product,
                image=image,
                alt_text=alt_text
            )
            created_images.append(product_image)
        
        return created_images

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