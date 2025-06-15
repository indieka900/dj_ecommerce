from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BrandViewSet, CategoryViewSet, ProductViewSet, 
    ReviewViewSet, CartViewSet, WishlistViewSet, OrderViewSet,
    ProductImageViewSet, ProductVariantViewSet, ParendCategoryViewSet
)

router = DefaultRouter()
router.register('brands', BrandViewSet)
router.register('parent-categories', ParendCategoryViewSet)
router.register('categories', CategoryViewSet)
router.register('products', ProductViewSet)
router.register('reviews', ReviewViewSet)
router.register('orders', OrderViewSet, basename='order')
router.register('cart', CartViewSet, basename='cart')
router.register('wishlist', WishlistViewSet, basename='wishlist')
router.register('product-images', ProductImageViewSet, basename='product-image')
router.register('product-variants', ProductVariantViewSet, basename='product-variant')

urlpatterns = [
    path('', include(router.urls)),
]