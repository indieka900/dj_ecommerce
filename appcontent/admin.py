from django.contrib import admin
from appcontent.models import Faq, About
from ecommerce.models import AppContent

admin.site.register(Faq)
admin.site.register(About)
admin.site.register(AppContent)

# Register your models here.
