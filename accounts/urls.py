from django.urls import path
from django.contrib.auth import views as a_views
from . import views

urlpatterns = [
    path('login/', a_views.LoginView.as_view(),  name='login'),
    path('logout/', a_views.LogoutView.as_view() , name='logout'),
]