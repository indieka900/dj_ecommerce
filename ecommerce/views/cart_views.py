from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Cart, CartItem, Product, Review
from .services import CartService, CommonService
from django.core.exceptions import ValidationError


@login_required(login_url='account')
def add_to_cart_view(request, product_id):
    if request.method == 'POST':
        if 'add-to-wishlist' in request.POST:
            return redirect(f'/add-wishlist/{product_id}/')
    try:
        # Fetch product
        product = Product.objects.get(id=product_id)
        
        # Prepare cart addition parameters
        params = {
            'user': request.user,
            'product': product,
            'quantity': int(request.POST.get('quantity', 1))
        }

        # Add variant information if product has variants
        if product.has_variants:
            params['size'] = request.POST.get('size')
            params['color'] = request.POST.get('color')

        # Add to cart
        CartService.add_to_cart(**params)
        
        messages.success(request, f"{product.title} added to cart!")
        return redirect('cart_detail')

    except Product.DoesNotExist:
        messages.error(request, "Product not found")
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
            **CommonService.get_common_context(request)
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
    