'''Use this for development'''

from .base import *


ALLOWED_HOSTS += ['127.0.0.1']
DEBUG = True

WSGI_APPLICATION = 'ecommerce_proj.wsgi.dev.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'onlineshop',
        'USER': 'root',
        'PASSWORD': '',
        'HOST':'localhost',
        'PORT':'3306',
        "OPTIONS": {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
                'charset': 'utf8mb4',
                "autocommit": True,
            }
    },
}