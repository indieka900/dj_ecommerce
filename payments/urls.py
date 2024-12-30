from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('initiate/<int:order_id>/', views.initiate_payment, name='initiate'),
    path('callback/', views.callback, name='callback'),
    path('waiting/<str:transaction_id>/', views.waiting_page, name='waiting_page'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('payment-cancelled/', views.payment_failed, name='payment_cancelled'),
    path('status/<str:transaction_id>/', views.check_payment_status, name='check_status'),
]