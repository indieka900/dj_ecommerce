from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from ..models import Cart, CartItem, Product

def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'ecommerce/cart.html', context)

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"{product.title} has been added to your cart.")
    return redirect('product_detail', pk=product_id)