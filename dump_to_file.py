import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_proj.settings.dev') 
django.setup()

with open('data1.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', '--indent', '2', stdout=f)
