from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Cart, CartItem, Product
from .product_views import common_data
from django.db import transaction
from django.core.exceptions import ValidationError

class CartService:
    """
    Service class to handle cart-related operations
    """
    @classmethod
    @transaction.atomic
    def add_to_cart(cls, user, product : Product, quantity=1, size=None, color=None):
        
        if product.quantity < quantity:
            raise ValidationError("Insufficient product quantity")
        
        # Get or create user's cart
        cart, _ = Cart.objects.get_or_create(user=user)
        try:
            cart_item = CartItem.objects.get(
                cart=cart, 
                product=product, 
                size=size, 
                color=color
            )
            cart_item.quantity += quantity
        except CartItem.DoesNotExist:
            cart_item = CartItem(
                cart=cart, 
                product=product, 
                quantity=quantity,
                size=size,
                color=color
            )
        cart_item.full_clean()
        cart_item.save()
        
        product.quantity -= quantity
        product.save()
        
        return cart_item

@login_required(login_url='account')
def add_to_cart_view(request, product_id):
    if request.method == 'POST':
        print(request.POST)
        try:
            product = Product.objects.get(id=product_id)
            cart_item = CartService.add_to_cart(
                user=request.user,
                product=product,
                quantity=int(request.POST.get('quantity', 1)),
                size=request.POST.get('size'),
                color=request.POST.get('color')
            )
            messages.success(request, "Product added to cart!")
        except ValidationError as e:
            messages.error(request, str(e))
        
        return redirect('cart_detail')

@login_required(login_url='account')
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cart_items.select_related('product').all()
        
        total_price = cart.total_price() if cart_items.exists() else 0
        
        context = {
            'cart_items': cart_items,  
            'total_price': total_price,
            'cart': cart,
            **common_data(request)
        }
        
        template = 'cart.html' if cart_items.exists() else 'cart-empty.html'
        return render(request, template, context)
    
    except Cart.DoesNotExist:
        return render(request, 'cart-empty.html')
    
