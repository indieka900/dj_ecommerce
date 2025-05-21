from blogs.models import Blog, Comment, BlogCategory
from .serializers import BlogSerializer, CommentSerializer, BlogCategorySerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action


class BlogViewSet(ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__category=category)
        return queryset
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        latest_blogs = self.get_queryset().order_by('-date_posted')[:5]
        serializer = self.get_serializer(latest_blogs, many=True)
        return Response(serializer.data)
    
class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        blog_id = self.request.query_params.get('blog')
        if blog_id:
            queryset = queryset.filter(blog__id=blog_id)
        return queryset