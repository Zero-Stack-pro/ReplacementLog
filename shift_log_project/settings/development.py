"""
Настройки для разработки
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Development-specific settings
# debug_toolbar опционален (установите django-debug-toolbar если нужен)
try:
    import debug_toolbar
    if DEBUG:
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    # debug_toolbar не установлен, пропускаем
    pass

