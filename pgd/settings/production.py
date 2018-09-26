from .base import *

DEBUG = False

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pgd',
        'USER': 'pgd',
        'PASSWORD': 'lordofallfiremen!',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

ALLOWED_HOSTS = ['pgd.pollvortex.com']

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'ubuntu-pgd'
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'PGD Železniki <info@pgd-zelezniki.si>'

# # EMAIL_USE_TLS = True
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = '52.59.193.205'
# # EMAIL_HOST_PASSWORD = 'bpdcuqqkibaexwvc'
# EMAIL_HOST_USER = 'mail@cargox.io'
# EMAIL_PORT = 1587

# EMAIL_SUBJECT_PREFIX = '[CargoX API] '


try:
    from .local import *
except ImportError:
    pass
