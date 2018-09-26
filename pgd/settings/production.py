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



try:
    from .local import *
except ImportError:
    pass
