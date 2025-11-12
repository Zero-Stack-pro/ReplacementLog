# Исправление проблемы со статическими файлами (CSS/JS)

## Проблема

После перехода на production настройки пропали стили (CSS) и перестали работать JavaScript файлы.

## Причина

В production режиме (`DEBUG=False`) Django не раздает статические файлы автоматически. В `urls.py` статические файлы подключены только для режима разработки:

```python
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

## Решение

Установлен и настроен **WhiteNoise** - стандартное решение для раздачи статических файлов в Django production без отдельного веб-сервера.

### 1. Установка WhiteNoise

Добавлен в `requirements.txt`:
```
whitenoise==6.8.2
```

### 2. Настройка middleware

Добавлен WhiteNoise middleware в `base.py` сразу после `SecurityMiddleware`:
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise для раздачи статики
    # ... остальные middleware
]
```

### 3. Настройка storage

В `production.py` установлен:
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

Это обеспечивает:
- **Сжатие** статических файлов (gzip)
- **Версионирование** через манифест (cache busting)
- **Оптимизацию** производительности

### 4. Сбор статических файлов

Выполнено:
```bash
python manage.py collectstatic --clear --noinput
```

Создан манифест `staticfiles.json` с хешами всех файлов.

## Результат

✅ WhiteNoise установлен и настроен
✅ Статические файлы собираются с манифестом
✅ CSS и JS файлы доступны в production
✅ Файлы сжимаются для оптимизации
✅ Кэширование работает корректно

## Проверка

Статические файлы должны быть доступны по адресам:
- `http://10.45.20.40:8000/static/css/style.css`
- `http://10.45.20.40:8000/static/js/main.js`

## Дополнительная информация

WhiteNoise автоматически:
- Раздает статические файлы через Django
- Сжимает файлы (gzip/brotli)
- Добавляет правильные заголовки кэширования
- Поддерживает версионирование через манифест

Для обновления статических файлов после изменений:
```bash
python manage.py collectstatic --noinput
sudo systemctl restart replacementlog.service
```

