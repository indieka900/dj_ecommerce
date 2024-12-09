from django.shortcuts import render, get_object_or_404
from blogs.models import Blog, Comment, BlogCategory
from ecommerce.views.services import CommonService

def blogs(request):
    blogs = Blog.objects.all()
    categories = BlogCategory.objects.all()
    context = {
        'blogs' : blogs,
        'b_categories' : categories,
        **CommonService.get_common_context(request)
    }
    return render(request, 'blog.html', context)

def blogs_by_category(request, cat):
    category = get_object_or_404(BlogCategory, category=cat)
    blogs = Blog.objects.filter(category=category)
    categories = BlogCategory.objects.all()
    
    context = {
        'blogs' : blogs,
        'b_categories' : categories,
        **CommonService.get_common_context(request)
    }
    return render(request, 'blog.html', context)

# Create your views here.
