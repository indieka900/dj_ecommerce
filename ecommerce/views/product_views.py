from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from ..models import Product, Category

def home(request):
    featured_products = Product.objects.filter(featured=True)[:4]
    categories = Category.objects.all()[:3]
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'path' : 'home',
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