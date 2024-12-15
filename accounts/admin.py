from django.contrib import admin
from accounts.models import CustomUser, ContactUs

admin.site.register(CustomUser)
admin.site.register(ContactUs)

# Register your models here.
