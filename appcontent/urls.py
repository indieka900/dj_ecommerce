from django.urls import path
from .views import home, about, faq, ComprehensiveDashboardView

urlpatterns = [
    path('', home, name='home'),
    path('api/dashboard/comprehensive/', ComprehensiveDashboardView.as_view(), name='comprehensive-dashboard'),
    path('about/', about, name='about'),
    path('faq/', faq, name='faq'),
]