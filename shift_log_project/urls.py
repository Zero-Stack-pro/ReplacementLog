"""
URL configuration for shift_log_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.urls import include, path
from django.views.decorators.cache import never_cache
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shift_log.urls')),
    path('testing/', include('testing.urls')),
]

# Добавляем обработку медиа файлов
if settings.DEBUG:
    # В режиме разработки используем стандартную обработку
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # В production раздаем медиа файлы через Django (временное решение)
    # ВАЖНО: Для production рекомендуется настроить nginx/apache для раздачи медиа файлов
    # для лучшей производительности
    @never_cache
    def media_serve(request, path, document_root=None, show_indexes=False):
        """
        Раздача медиа файлов в production.
        ВАЖНО: Для production рекомендуется настроить веб-сервер (nginx/apache)
        для раздачи медиа файлов напрямую, без Django.
        """
        if not document_root:
            document_root = settings.MEDIA_ROOT
        
        try:
            return serve(request, path, document_root=document_root, show_indexes=show_indexes)
        except Http404:
            return HttpResponse('Файл не найден', status=404)
    
    urlpatterns += [
        path(f'{settings.MEDIA_URL.strip("/")}/<path:path>', media_serve, name='media'),
    ]
