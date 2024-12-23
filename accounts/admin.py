from django.contrib import admin
from accounts.models import CustomUser, ContactUs, Address

admin.site.register(CustomUser)
admin.site.register(ContactUs)
admin.site.register(Address)

# Register your models here.
