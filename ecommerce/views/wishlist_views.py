from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from ecommerce.models import Wishlist, WishlistItem, Product
from django.contrib.auth.decorators import login_required
from django.db import transaction
from ecommerce.views.product_views import common_data
from ecommerce.views.cart_views import CartService

class WishListService:
    
    @classmethod
    @transaction.atomic
    def add_to_wishlist(self, user, product):
        w_list, _ = Wishlist.objects.get_or_create(user=user)
        try:
            wishlist_item = WishlistItem.objects.get(wishlist=w_list, product=product)
        except WishlistItem.DoesNotExist:
            wishlist_item = WishlistItem.objects.create(
                wishlist = w_list, product=product
            )
        return wishlist_item
    
@login_required(login_url='account')
def add_to_wishlist(request, product_id):
    try: 
        product = get_object_or_404(Product, pk=product_id)
        WishListService.add_to_wishlist(
            user=request.user,
            product=product
        )
    except:
        pass
    
    return redirect('wishlist')
    
@login_required(login_url='account')
def wishlist_detail(request):
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_items = wishlist.wishlist_items.select_related('product').all()
        context = {
            'w_items' : wishlist_items,
            **common_data(request),
        }
        template = 'wishlist.html' if wishlist_items.exists() else 'wishlist-empty.html'
        return render(request, template, context)
    except Wishlist.DoesNotExist:
        return render(request, 'wishlist-empty.html')
    
@login_required(login_url='account')
def delete_wishlist_item(request, pk):
    try:
        w_item = get_object_or_404(WishlistItem, pk=pk)
        if request.method == "POST":
            if "delete" in request.POST:
                w_item.delete()
            if "add-to-cart" in request.POST:
                CartService.add_to_cart(request.user, w_item.product)
                return redirect('cart_detail')
    except:
        pass
    
    return redirect('wishlist')