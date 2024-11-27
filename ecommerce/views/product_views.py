from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from ..models import Product, Category, AppContent, Slider, Wishlist, Cart

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
    featured_products = Product.objects.filter(featured=True)[:4]
    categories = Category.objects.all()[:3]
    context = {
        'featured_products': featured_products,
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
    context = {
        'product': product,
    }
    return render(request, 'ecommerce/product_detail.html', context)