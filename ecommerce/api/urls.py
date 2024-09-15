from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BrandViewSet, CategoryViewSet, ProductViewSet, ReviewViewSet, OrderViewSet, CartViewSet, WishlistViewSet

router = DefaultRouter()
router.register(r'brands', BrandViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')

urlpatterns = [
    path('', include(router.urls)),
]