from blogs.models import Blog, BlogCategory
from django.db import models
from django.shortcuts import get_object_or_404

class BlogService:
    @classmethod
    def get_blogs_with_optimized_query(cls, category=None):
        """
        Retrieve blogs with optimized database querying
        
        Args:
            category (BlogCategory, optional): Filter blogs by specific category
        
        Returns:
            QuerySet: Optimized blog queryset
        """
        # Base query with related data prefetched
        blogs = Blog.objects.select_related(
            'category' 
        ).prefetch_related(
            'comments'
        ).order_by('-date_posted')
        
        if category:
            blogs = blogs.filter(category=category)
        
        return blogs
    
    @classmethod
    def get_blog_categories(cls):
        """
        Retrieve blog categories with optimized query
        
        Returns:
            QuerySet: Blog categories with blog count
        """
        return BlogCategory.objects.annotate(
            blog_count=models.Count('blog', distinct=True)
        )
        
    @classmethod
    def get_blog_with_navigation(cls, slug):
        """
        Retrieve a blog with its previous and next blogs
        
        Args:
            slug (str): Slug of the current blog
        
        Returns:
            tuple: (current blog, previous blog, next blog)
        """
        # Get the current blog
        current_blog = get_object_or_404(
            Blog.objects.select_related('category'),
            slug=slug
        )
        
        # Find previous and next blogs based on date posted
        previous_blog = Blog.objects.filter(
            date_posted__lt=current_blog.date_posted
        ).order_by('-date_posted').first()
        
        next_blog = Blog.objects.filter(
            date_posted__gt=current_blog.date_posted
        ).order_by('date_posted').first()
        
        return current_blog, previous_blog, next_blog