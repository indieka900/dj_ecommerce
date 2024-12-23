from django.urls import path
from .views import product_views, cart_views, order_views, wishlist_views

urlpatterns = [
    path('', product_views.home, name='home'),
    path('products/', product_views.product_list, name='product_list'),
    path('product/<int:pk>/', product_views.product_detail, name='product_detail'),
    path('store/', product_views.directory, name='store'),
    path('products/<slug>/', product_views.products_by_parent_c, name='product_by_pcategory'),
    path('shop/<slug>/', product_views.products_by_category, name='product_by_category'),
    path('search_results/', product_views.search_products, name='search_products'),
    path('cart/', cart_views.cart_detail, name='cart_detail'),
    path('cart-item/<int:pk>/', cart_views.update_cartItem, name='cart_item'),
    path('add-to-cart/<int:product_id>/', cart_views.add_to_cart_view, name='add_to_cart'),
    path('checkout/', order_views.checkout, name='checkout'),
    path('create-order/', order_views.create_order, name='create-order'),
    path('add-review/<int:product_id>/', cart_views.addReview, name='add_review'),
    path('wishlist/', wishlist_views.wishlist_detail, name='wishlist'),
    path('add-wishlist/<int:product_id>/', wishlist_views.add_to_wishlist, name='add-to-wishlist'),
    path('del-wishlist-item/<int:pk>/', wishlist_views.delete_wishlist_item),
]