"""
Django settings for shift_log_project project.

Используется модульная структура настроек:
- settings/base.py - базовые настройки
- settings/development.py - настройки для разработки
- settings/production.py - настройки для production

Окружение определяется переменной DJANGO_ENVIRONMENT (по умолчанию 'development')
"""

# Импортируем настройки в зависимости от окружения
from .settings import *
