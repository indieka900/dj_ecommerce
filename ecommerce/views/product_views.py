from django.shortcuts import render, get_object_or_404, redirect
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
    context = {
        'parent_categories' : parent_categories,
        **CommonService.get_common_context(request)
    }
    return render(request, 'store-directory.html', context)

def products_by_parent_c(request, slug):
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 2)
    
    # Retrieve products with pagination
    products, paginator, parent_category, categories = ProductService.get_products_by_parent_category(
        slug, 
        page_number=page_number, 
        per_page=int(per_page)
    )
    
    # Check if page is out of range
    if products is None:
        return render(request, 'shop-v5-product-not-found.html', {'message': 'Category not found'})
    context = {
        'products' : products,
        'paginator' : paginator,
        'categor' : categories,
        'cgry_title' : parent_category,
        **CommonService.get_common_context(request)
    }
    return render(request, 'shop-v1-root-category.html', context)

def products_by_category(request, slug):
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 2)
    
    # Retrieve products with pagination
    products, paginator, parent_category = ProductService.get_products_by_category(
        slug, 
        page_number=page_number, 
        per_page=int(per_page)
    )
    
    # Check if page is out of range
    if products is None:
        return render(request, 'shop-v5-product-not-found.html', {'message': 'Category not found'})
    context = {
        'products' : products,
        'paginator' : paginator,
        'cgry' : parent_category,
        **CommonService.get_common_context(request)
    }
    return render(request, 'shop-v3-sub-sub-category.html', context)

def search_products(request):
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    query = request.GET.get('query', '').strip()
    category_slug = request.GET.get('category', 'all')
    
    # Handle empty query
    if not query:
        return redirect('store')
    
    # Retrieve category if specified
    category = None
    if category_slug and category_slug != 'all':
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            # messages.error(request, "Invalid category selected")
            return redirect('store')
    
    # Retrieve products with pagination
    products, paginator = ProductService.search_products(
        query,
        category=category,
        page_number=int(page_number),
        per_page=int(per_page)
    )
    parent_categories = ParentCategory.objects.prefetch_related(
        Prefetch(
            'category_set', 
            queryset=Category.objects.all(), 
            to_attr='subcategories'
        )
    )
    
    # Handle no results
    if not products:
        # messages.info(request, f"No products found for '{query}'")
        return render(request, 'shop-v5-product-not-found.html')
    
    # Prepare context
    context = {
        'products': products,
        'query': query,
        'paginator': paginator,
        'parent_categories' : parent_categories,
        **CommonService.get_common_context(request)
    }
    return render(request, 'shop-v6-search-results.html', context)