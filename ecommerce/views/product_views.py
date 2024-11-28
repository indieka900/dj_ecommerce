from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from ..models import (
    Product, Category, AppContent, Slider, Wishlist, Cart,
    ProductImage, ProductVariant
)

def common_data(request):
    app_data = AppContent.objects.all().first()
    sliders = Slider.objects.filter(app=app_data)
    # cart = Cart.objects.get(user=request.user)
    
    # # Fetch cart items with related products
    # cart_items = cart.cart_items.select_related('product')
    
    # # Calculate total items
    # total_items = cart_items.count()
    
    # # Calculate total price
    # total_price = sum(
    #     item.product.calculate_selling_price() 
    #     for item in cart_items
    # )
    return {
        'app_data': app_data,
        'sliders' : sliders,
        'categories' : Category.objects.all(),
        # 'total_items' : total_items, 
        # 'total_price' : total_price,
        # 'pages': Page.objects.all(),
    }

def home(request):
    latest_products = Product.objects.all()[:4]
    categories = Category.objects.all()[:3]
    context = {
        'latest_products': latest_products,
        'categories': categories,
        'path' : 'home',
        **common_data(request)
    }
    return render(request, 'home.html', context)

def product_list(request):
    products = Product.objects.all()
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'ecommerce/product_list.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    p_images = ProductImage.objects.filter(product=product)
    s_products = Product.objects.filter(category=product.category)
    variants = ProductVariant.objects.filter(product=product)
    unique_colors = list(set(variant.color for variant in variants if variant.color))
    context = {
        'product': product,
        'images' : p_images,
        'similar_products' : s_products,
        'variants' : variants,
        'unique_colors': unique_colors,
        **common_data(request)
    }
    return render(request, 'single-product.html', context)