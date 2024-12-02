from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Cart, CartItem, Product, Review
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
    
    @classmethod
    @transaction.atomic
    def update_cart_item(cls, cart_item:CartItem, new_quantity):
        
        product = cart_item.product
        
        # Validate quantity
        if new_quantity < 1:
            raise ValidationError("Quantity must be at least 1.")
        
        # Check if enough product is available
        available_quantity = product.quantity + cart_item.quantity
        if new_quantity > available_quantity:
            raise ValidationError(f"Only {available_quantity} items available.")
        
        # Calculate quantity difference
        qty_diff = new_quantity - cart_item.quantity
        
        # Update product and cart item quantities
        product.quantity -= qty_diff
        cart_item.quantity = new_quantity
        
        # Save changes
        product.save()
        cart_item.save()
        
        return cart_item

    @classmethod
    @transaction.atomic
    def remove_cart_item(cls, cart_item:CartItem):
        product = cart_item.product
        
        # Return product quantity back to inventory
        product.quantity += cart_item.quantity
        product.save()
        
        # Delete the cart item
        cart_item.delete()
        
        return product

@login_required(login_url='account')
def add_to_cart_view(request, product_id):
    if request.method == 'POST':
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
    
@login_required(login_url='account')
def update_cartItem(request, pk):
    try:
        # Fetch cart item 
        cart_item = get_object_or_404(CartItem, pk=pk)

        if request.method == 'POST':
            # Handle deletion
            if "delete" in request.POST:
                product = CartService.remove_cart_item(cart_item)
                messages.success(request, f"{product.title} removed from cart.")
                return redirect('cart_detail')

            # Handle quantity update
            if "update" in request.POST:
                try:
                    new_qty = int(request.POST['quantity'])
                    
                    # Use the service method to update cart item
                    updated_cart_item = CartService.update_cart_item(cart_item, new_qty)
                    
                    messages.success(request, f"{updated_cart_item.product.title} quantity updated to {new_qty}.")
                
                except ValidationError as e:
                    messages.error(request, str(e))
                except ValueError:
                    messages.error(request, "Invalid quantity entered.")
    
    except Exception as e:
        # Log the error or handle it appropriately
        messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect('cart_detail')

def addReview(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
            email = user.email
            name = user.first_name
        else:
            name = request.POST['name']
            email = request.POST['email']
        review_title = request.POST['review_title']
        review = request.POST['review']
        rating = float(request.POST['rating'])
        rev = Review(
            product=product,
            name = name,
            email = email,
            review_title = review_title,
            review = review,
            rating = rating
        )
        rev.save()
        return redirect(f'/product/{product_id}/')
    