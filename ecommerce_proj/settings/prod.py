from .base import *
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

DEBUG = False
ALLOWED_HOSTS += ['*']
WSGI_APPLICATION = 'ecommerce_proj.wsgi.prod.application'

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Parse the database URL
    db_config = dj_database_url.parse(DATABASE_URL)
    
    # Add SSL configuration for Render PostgreSQL
    db_config['OPTIONS'] = {
        'sslmode': 'require',
    }
    
    DATABASES = {
        'default': db_config
    }


SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000 
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True