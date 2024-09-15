from django.contrib import admin
from .models import models_

for model in models_:
    admin.site.register(model)

# Register your models here.
