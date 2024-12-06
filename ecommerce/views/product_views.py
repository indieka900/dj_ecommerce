from django.shortcuts import render, get_object_or_404
from .services import CommonService, ProductService, Category, ParentCategory
from django.db.models import Prefetch
from ecommerce.models import Product

def home(request):
    """
    Render home page with latest products and categories.
    """
    context = {
        'latest_products': ProductService.get_latest_products(),
        'featured_products' : ProductService.get_featured_products(),
        'categories': ProductService.get_featured_categories(),
        'path': 'home',
        **CommonService.get_common_context(request)
    }
    print(context)
    return render(request, 'home.html', context)

def product_list(request):
    """
    Render paginated product list.
    """
    page_number = request.GET.get('page', 1)
    
    page_obj, paginator = ProductService.get_product_list(
        page_number=page_number
    )
    
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        **CommonService.get_common_context(request)
    }
    print(context)
    
    return render(request, 'ecommerce/product_list.html', context)

def product_detail(request, pk):
    """
    Render detailed product page.
    """
    try:
        product_details = ProductService.get_product_detail(pk)
        
        context = {
            **product_details,
            **CommonService.get_common_context(request)
        }
        
        return render(request, 'single-product.html', context)
    
    except Product.DoesNotExist:
        # Handle product not found scenario
        return render(request, '404.html'), 404
    
def directory(request):
    parent_categories = ParentCategory.objects.prefetch_related(
        Prefetch(
            'category_set', 
            queryset=Category.objects.all(), 
            to_attr='subcategories'
        )
    )
    print(parent_categories)
    context = {
        'parent_categories' : parent_categories,
        **CommonService.get_common_context(request)
    }
    return render(request, 'store-directory.html', context)