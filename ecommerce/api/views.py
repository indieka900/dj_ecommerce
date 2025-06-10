from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from ecommerce.models import Brand, Category, Product, Review, Order, Cart, Wishlist, ProductImage, ProductVariant
from .serializers import (
    BrandSerializer, CategorySerializer, ProductSerializer, ReviewSerializer, 
    OrderSerializer, CartSerializer, WishlistSerializer, ProductImageSerializer, ProductVariantSerializer
)
from appcontent.utils import IsAdminUserOrReadOnly
from django.db.models import Sum

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminUserOrReadOnly]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('variants', 'images').all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__product').annotate(
        total_items=Sum('items__quantity')
    )
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    
    def perform_create(self, serializer):
        product = self.request.data.get('product')
        if not product:
            raise ValueError("Product must be specified for the image.")
        try:
            product = Product.objects.get(id=product)
        except Product.DoesNotExist:
            raise ValueError("Product with the specified ID does not exist.")
        serializer.save(product=product)
    
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        product = self.request.data.get('product')
        if not product:
            raise ValueError("Product must be specified for the variant.")
        serializer.save(product_id=product)