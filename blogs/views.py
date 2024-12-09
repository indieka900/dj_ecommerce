from django.shortcuts import render, get_object_or_404
from blogs.models import Blog, Comment, BlogCategory

def blogs(request):
    blogs = Blog.objects.all()
    categories = BlogCategory.objects.all()
    context = {
        'blogs' : blogs,
        'b_categories' : categories
    }
    return render(request, 'blog.html', context)

def blogs_by_category(request, cat):
    category = get_object_or_404(BlogCategory, category=cat)
    blogs = Blog.objects.filter(category=category)
    categories = BlogCategory.objects.all()
    
    context = {
        'blogs' : blogs,
        'b_categories' : categories
    }
    return render(request, 'blog.html', context)

# Create your views here.
