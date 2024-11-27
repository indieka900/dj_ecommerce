from django.urls import path
from django.contrib.auth import views as a_views
from . import views

urlpatterns = [
    # path('login/', a_views.LoginView.as_view(template_name = 'account.html'),  name='login'),
    path('login/', views.login_user,  name='login'),
    path('logout/', a_views.LogoutView.as_view() , name='logout'),
    path('account/', views.SignupView.as_view(), name='account'),
]