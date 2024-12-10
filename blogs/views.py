from django.shortcuts import render, get_object_or_404
from blogs.models import Blog, Comment, BlogCategory
from ecommerce.views.services import CommonService
from blogs.forms import CommentForm

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

def blog(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    
    if request.method == 'POST':
        print(request.POST)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.save() 
    comments = Comment.objects.filter(blog=blog)

    context = {
        'blog' : blog,
        'comments' : comments,
        **CommonService.get_common_context(request)
    }
    
    return render(request, 'blog-detail.html', context)

# Create your views here.
