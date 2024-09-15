from django.urls import path
from .views import product_views, cart_views, order_views

urlpatterns = [
    path('', product_views.home, name='home'),
    path('products/', product_views.product_list, name='product_list'),
    path('product/<int:pk>/', product_views.product_detail, name='product_detail'),
    path('cart/', cart_views.cart_detail, name='cart_detail'),
    path('checkout/', order_views.checkout, name='checkout'),
]