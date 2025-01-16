from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ecommerce.forms import CheckoutForm
from ..models import Order, Cart
from django.db import transaction
from .services import OrderService, CommonService
from accounts.models import Address
from django.urls import reverse
from payments.services import PaymentService
from payments.utils import format_phone_number

@login_required(login_url='account')
def checkout(request):
    if request.method != 'GET':
        print(request.POST)
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cart_items.select_related('product').all()
        
        total_price = cart.total_price() if cart_items.exists() else 0
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    form = CheckoutForm()
    context = {
        'cart_items': cart_items,  
        'total_price': total_price,
        'cart': cart,
        'form': form,
        **CommonService.get_common_context(request)
    }
    return render(request, 'checkout.html', context)

@login_required(login_url='account')
def create_order(request):
    if request.method != 'POST':
        return redirect('cart:cart_detail')
    
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    
    form = CheckoutForm(request.POST)
    try:
        phone = format_phone_number(request.POST.get('billing_phone'))
    except ValueError as e:
        messages.error(request, 'Invalid phone number.')
        raise ValueError(f"Invalid phone number: {str(e)}")
    
    if form.is_valid():
        with transaction.atomic():
            # Create billing address
            billing_address = Address.objects.create(
                user=request.user,
                first_name=form.cleaned_data['billing_first_name'].capitalize(),
                last_name=form.cleaned_data['billing_last_name'].capitalize(),
                email=form.cleaned_data['billing_email'],
                phone=format_phone_number(form.cleaned_data['billing_phone']),
                street_address=form.cleaned_data['billing_street_address'],
                apartment=form.cleaned_data['billing_apartment'],
                city=form.cleaned_data['billing_city'],
                county=form.cleaned_data['billing_county'],
                postal_code=form.cleaned_data['billing_postal_code']
            )
            
            # Handle shipping address
            if not form.cleaned_data['different_shipping_loc']:
                shipping_address = billing_address
            else:
                shipping_address = Address.objects.create(
                    user=request.user,
                    first_name=form.cleaned_data['shipping_first_name'].capitalize(),
                    last_name=form.cleaned_data['shipping_last_name'].capitalize(),
                    email=form.cleaned_data['shipping_email'],
                    phone=format_phone_number(form.cleaned_data['shipping_phone']),
                    street_address=form.cleaned_data['shipping_street_address'],
                    apartment=form.cleaned_data['shipping_apartment'],
                    city=form.cleaned_data['shipping_city'],
                    county=form.cleaned_data['shipping_county'],
                    postal_code=form.cleaned_data['shipping_postal_code']
                )
    else:
        print(form.errors)
        messages.error(request, 'Please correct the errors below.')
        return redirect('checkout')
    
    payment_method = request.POST.get('payment-method')
    if not payment_method:
        messages.error(request, 'Please select a payment method.')
        return redirect('checkout')

    notes=form.cleaned_data['order_notes']

    try:
        # print(shipping_address, billing_address)
        with transaction.atomic():
            order = OrderService.create_order_from_cart(
                cart=cart,
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_method=payment_method,
                notes=notes
            )
            host = request.get_host()
            call_back_url = f'https://{host}{reverse("callback")}'
            print(call_back_url)
            payment_service = PaymentService()
            return_url = request.build_absolute_uri(reverse("payment_success"))
            cancel_url = request.build_absolute_uri(reverse("payment_cancelled"))
            tr = payment_service.create_payment_for_order(
                order, request.user, payment_method, 
                phone_number = phone,
                return_url = return_url,
                cancel_url = cancel_url,
                call_back_url = call_back_url
            )
            messages.success(
                request,
                f'Order {order.order_number} created successfully.'
            )
            if payment_method == 'mpesa':
                return redirect('waiting_page', transaction_id=tr.id)
            if payment_method == 'paypal' and tr.payment_url:
                return redirect(tr.payment_url)
            return HttpResponse('Order created successfully.')
    except Exception as e:
        print(e)
        messages.error(
            request,
            'There was an error processing your order. Please try again.'
        )
        return redirect('checkout')

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