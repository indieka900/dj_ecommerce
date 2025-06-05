from django.urls import path
from . import views

urlpatterns = [
    path('', views.blogs, name='blogs'),
    path('blog-search/', views.search_blogs, name='blog-search'),
    path('by_cat/<cat>/', views.blogs_by_category, name='blogs_by_category'),
    path('<slug>/', views.blog, name='blog-detail-'),
]