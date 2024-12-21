from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Order, OrderItem, Cart
from django.db import transaction
from .services import OrderService
from accounts.models import Address

@login_required
def create_order(request):
    if request.method != 'POST':
        return redirect('cart:cart_detail')

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')

    # Get or validate shipping address
    shipping_address_id = request.POST.get('shipping_address')
    try:
        shipping_address = Address.objects.get(
            id=shipping_address_id,
            user=request.user
        )
    except Address.DoesNotExist:
        messages.error(request, 'Please select a valid shipping address.')
        return redirect('checkout:checkout')

    # Get or validate billing address
    billing_address_id = request.POST.get('billing_address')
    billing_address = None
    if billing_address_id:
        try:
            billing_address = Address.objects.get(
                id=billing_address_id,
                user=request.user
            )
        except Address.DoesNotExist:
            messages.error(request, 'Please select a valid billing address.')
            return redirect('checkout:checkout')

    payment_method = request.POST.get('payment_method')
    if not payment_method:
        messages.error(request, 'Please select a payment method.')
        return redirect('checkout:checkout')

    notes = request.POST.get('notes', '')

    try:
        with transaction.atomic():
            order = OrderService.create_order_from_cart(
                cart=cart,
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_method=payment_method,
                notes=notes
            )
            messages.success(
                request,
                f'Order {order.order_number} created successfully.'
            )
            return redirect('orders:order_detail', pk=order.id)
    except Exception as e:
        messages.error(
            request,
            'There was an error processing your order. Please try again.'
        )
        return redirect('checkout:checkout')

@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if not order.can_cancel:
        messages.error(
            request,
            'This order cannot be cancelled.'
        )
        return redirect('orders:order_detail', pk=order.id)
    
    try:
        with transaction.atomic():
            order.status = "Cancelled"
            order.save()
            messages.success(
                request,
                f'Order {order.order_number} has been cancelled.'
            )
    except Exception as e:
        messages.error(
            request,
            'There was an error cancelling your order. Please try again.'
        )
    
    return redirect('orders:order_detail', pk=order.id)