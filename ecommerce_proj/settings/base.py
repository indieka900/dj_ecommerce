from datetime import timedelta
from pathlib import Path
import socket
import os
from dotenv import load_dotenv

load_dotenv()

def str_to_bool(value):
    return value.lower() in ['true', '1', 't', 'y', 'yes']

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-3fkp0m^xnffb-@^al^algzx__*!&^-a4esqmm548i2^9-!y7k&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['9762-102-140-250-158.ngrok-free.app', '*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'accounts',
    'ecommerce',
    'payments',
    'rest_framework',
    'blogs',
]

AUTH_USER_MODEL = 'accounts.CustomUser'

LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/account/login/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Ensure CSRF is configured
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://9762-102-140-250-158.ngrok-free.app',
]

ROOT_URLCONF = 'ecommerce_proj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Rest Framework settings
REST_FRAMEWORK = {
    
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "rest_framework.permissions.IsAdminUser",
       # 'rest_framework_simplejwt.authentication.JWTAuthentication',

    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),     
    
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=100),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_TZ = True
USE_I18N = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
MEDIA_URL = 'ecommerce_proj/media/'
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'build/static')]
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_USE_TLS = str_to_bool(os.environ.get('EMAIL_USE_TLS', 'False'))
EMAIL_USE_SSL = str_to_bool(os.environ.get('EMAIL_USE_SSL', 'False'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('ACCOUNTS_EMAIL_PASSWORD')

# Safaricom daraja credentials
CONSUMER_KEY = os.getenv('CONSUMER_KEY') 
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')  
SHORTCODE = os.getenv('SHORTCODE')  
PASSKEY = os.getenv('PASSKEY') 
BASE_URL = os.getenv('BASE_URL')

#Paypoal credentials 
PAYPAL_ID = os.getenv('PAYPAL_ID')
PAYPAL_SECRET = os.getenv('PAYPAL_SECRET')
PAYPAL_BASE_URL = os.getenv('PAYPAL_BASE_URL')
PAYPAL_MODE = os.getenv('PAYPAL_MODE')
PAYPAL_RECEIVER_EMAIL = os.getenv('PAYPAL_RECEIVER_EMAIL')
PAYPAL_TEST = True

# print(f"CONSUMER_KEY: {CONSUMER_KEY}, CONSUMER_SECRET: {CONSUMER_SECRET}, SHORTCODE: {SHORTCODE}, PASSKEY: {PASSKEY}, BASE_URL: {BASE_URL}")  