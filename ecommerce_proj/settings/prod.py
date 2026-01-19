from .base import *
from dotenv import load_dotenv
import dj_database_url
import mimetypes

load_dotenv()

mimetypes.add_type("application/javascript", ".js", True)
mimetypes.add_type("application/javascript", ".mjs", True)

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False 
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']

# Enhanced MIME types for WhiteNoise
WHITENOISE_MIMETYPES = {
    '.js': 'application/javascript',
    '.mjs': 'application/javascript',
    '.jsx': 'application/javascript',
    '.ts': 'application/javascript',
    '.tsx': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.map': 'application/json',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.svg': 'image/svg+xml',
}

# Static files configuration
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'dist', 'assets'),
    os.path.join(BASE_DIR, 'dist'),
]

# Production settings
DEBUG = False
ALLOWED_HOSTS += ['dj-ecommerce-xevb.onrender.com', 'localhost', '127.0.0.1']
MEDIA_URL = '/media/'
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
