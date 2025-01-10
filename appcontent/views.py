from django.shortcuts import render
from ecommerce.views.services import CommonService, ProductService
from appcontent.models import Faq, About


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

def about(request):
    """
    Render about page.
    """
    context = {
        'path': 'about',
        **CommonService.get_common_context(request)
    }
    return render(request, 'about.html', context)

def faq(request):
    """
    Render FAQ page.
    """
    faqs = Faq.objects.all()
    context = {
        'path': 'faq',
        'faqs': faqs,
        **CommonService.get_common_context(request)
    }
    return render(request, 'faq.html', context)
