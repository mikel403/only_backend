from .common import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

FORCE_SCRIPT_NAME = '/djangoapp'

# SECURITY WARNING: keep the secret key used in production secret!


ALLOWED_HOSTS = ["cisiad.uned.es","www.cisiad.uned.es","62.204.199.21","62.204.199.21","127.0.0.1","localhost","10.195.9.104","www.cisiad.ia.uned.es","cisiad.ia.uned.es"]

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["DB_NAME"],
        "HOST": os.environ["DB_HOST"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
    }
}


CSRF_TRUSTED_ORIGINS = [
    'https://www.cisiad.uned.es',  # add your domain here
    "https://cisiad.uned.es",
]

CORS_ALLOWED_ORIGINS = [
    "https://www.cisiad.uned.es",
    "https://cisiad.uned.es",
]