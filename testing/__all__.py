"""
Публичный API модуля тестирования функционала.

Экспортирует основные классы и функции для использования в других частях приложения.
"""

from .models import (Feature, FeatureAttachment, FeatureComment,
                     FeatureStatusHistory, TestProject)
from .services.feature_service import (FeatureService, NotificationService,
                                       TestProjectService)

__all__ = [
    # Модели
    'TestProject',
    'Feature',
    'FeatureComment',
    'FeatureAttachment',
    'FeatureStatusHistory',
    
    # Сервисы
    'FeatureService',
    'NotificationService',
    'TestProjectService',
]
