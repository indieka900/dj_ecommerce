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

# Database
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
}

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    os.environ.get('FRONTEND_URLq', 'http://localhost:5173'),
    'https://dj-ecommerce-xevb.onrender.com',
]

CSRF_TRUSTED_ORIGINS = [
    'https://dj-ecommerce-xevb.onrender.com',
    'http://localhost:5173',
]