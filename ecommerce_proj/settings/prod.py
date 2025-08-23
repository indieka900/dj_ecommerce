from .base import *
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

DEBUG = False
ALLOWED_HOSTS += ['*']
WSGI_APPLICATION = 'ecommerce_proj.wsgi.prod.application'

DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
