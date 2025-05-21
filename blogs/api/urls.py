from django.urls import path, include
from .views import (
    BlogViewSet, CommentViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('blogs', BlogViewSet, basename='blog')
router.register('comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
]