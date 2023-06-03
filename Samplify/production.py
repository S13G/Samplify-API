from .settings import *

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", False, cast=bool)

ALLOWED_HOSTS = []

CSRF_TRUSTED_ORIGINS = ["https://" + host for host in ALLOWED_HOSTS]
