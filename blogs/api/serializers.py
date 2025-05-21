from blogs.models import Blog, Comment, BlogCategory
from rest_framework import serializers

class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ['id', 'category']
        read_only_fields = ['id']

class BlogSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Blog
        fields = ['id', 'title', 'author',  'category', 'image' , 'date_posted', 'slug', 'content',]
        read_only_fields = ['id', 'date_posted', 'slug']
        
    def get_category(self, obj :Blog):
        return obj.category.category
        
class CommentSerializer(serializers.ModelSerializer):
    blog = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'blog', 'full_name', 'email', 'website', 'text', 'added_at']
        read_only_fields = ['id', 'added_at']
        
    def get_blog(self, obj: Comment):
        return obj.blog.title