"""
Настройки для разработки
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Development-specific settings
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

