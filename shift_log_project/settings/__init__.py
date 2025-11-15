"""
Django settings модуль
"""
from pathlib import Path
import os

# Определяем окружение из переменной окружения
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .development import *







