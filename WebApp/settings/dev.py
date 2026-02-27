from .common import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1","localhost"]
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "default_secret_key")

PUBLIC_MEDIA_BASE_URL = os.environ.get(
    "PUBLIC_MEDIA_BASE_URL",
    "http://localhost:8000"
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "aplicacion"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "USER": os.getenv("DB_USER", "aplicacion"),
        "PASSWORD": os.getenv("DB_PASSWORD", "default_db"),
    }
}

CORS_ALLOW_ALL_ORIGINS = True