from django.shortcuts import render
from blogs.models import Blog, Comment, BlogCategory

def blogs(request):
    blogs = Blog.objects.all()
    categories = BlogCategory.objects.all()
    context = {
        'blogs' : blogs,
        'b_categories' : categories
    }
    return render(request, 'blog.html', context)

# Create your views here.
