from .base import *
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# CRITICAL: Add mimetypes for WhiteNoise to handle JS modules correctly
WHITENOISE_MIMETYPES = {
    '.js': 'application/javascript',
    '.mjs': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.map': 'application/json',
}

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'dist', 'assets'),
]

DEBUG = False
ALLOWED_HOSTS += ['*']
WSGI_APPLICATION = 'ecommerce_proj.wsgi.prod.application'

DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
