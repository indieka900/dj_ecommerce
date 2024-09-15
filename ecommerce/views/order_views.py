from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Order, OrderItem, Cart

@login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)
    if request.method == 'POST':
        # Process the order
        order = Order.objects.create(user=request.user, total_price=cart.total_price)
        for cart_item in cart.cartitem_set.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        cart.cartitem_set.all().delete()
        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_confirmation', order_id=order.id)
    
    context = {
        'cart': cart,
    }
    return render(request, 'ecommerce/checkout.html', context)