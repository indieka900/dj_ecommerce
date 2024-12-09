from django.contrib import admin
from blogs.models import my_models

for model in my_models:
    admin.site.register(model)

# Register your models here.
