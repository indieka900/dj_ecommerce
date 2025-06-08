from django.urls import path, include
from .views import (
    BlogViewSet, CommentViewSet, BlogCategoryViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('blogs', BlogViewSet, basename='blog')
router.register('comments', CommentViewSet, basename='comment')
router.register('categories', BlogCategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]