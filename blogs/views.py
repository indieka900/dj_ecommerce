from django.shortcuts import render, get_object_or_404, redirect
from blogs.models import Blog, Comment, BlogCategory
from ecommerce.views.services import CommonService
from blogs.services import BlogService
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
    """
    View to display blogs filtered by category
    """
    category = get_object_or_404(BlogCategory, category=cat)
    blogs = BlogService.get_blogs_with_optimized_query(category)
    categories = BlogService.get_blog_categories()
    print(categories)
    
    context = {
        'blogs': blogs,
        'b_categories': categories,
        'selected_category': category,
        **CommonService.get_common_context(request)
    }
    return render(request, 'blog.html', context)


def blog(request, slug):
    """
    View to display blog details with navigation
    """
    # Get current, previous, and next blogs
    current_blog, previous_blog, next_blog = BlogService.get_blog_with_navigation(slug)
    
    # Handle comment submission
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = current_blog
            comment.save()
            return redirect('blog_detail', slug=slug)
    
    comments = Comment.objects.filter(blog=current_blog).order_by('-added_at')
    
    # Prepare context
    context = {
        'blog': current_blog,
        'previous_blog': previous_blog,
        'next_blog': next_blog,
        'comments': comments,
        **CommonService.get_common_context(request)
    }
    
    return render(request, 'blog-detail.html', context)

# Create your views here.
