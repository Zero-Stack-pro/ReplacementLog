# Исправление ошибки 500

## Проблема

При переходе на production настройки возникла ошибка 500:
```
ValueError: Missing staticfiles manifest entry for 'css/style.css'
```

## Причина

В production настройках использовался `ManifestStaticFilesStorage`, который требует:
1. Сбор статических файлов с манифестом (`collectstatic`)
2. Наличие файла `staticfiles.json` с манифестом

## Решение

1. **Изменен STATICFILES_STORAGE** в `production.py`:
   - Было: `ManifestStaticFilesStorage`
   - Стало: `StaticFilesStorage` (обычное хранилище)

2. **Собраны статические файлы**:
   ```bash
   python manage.py collectstatic --noinput
   ```

## Результат

✅ Ошибка 500 исправлена
✅ Статические файлы собраны (163 файла)
✅ Приложение работает корректно

## Альтернативное решение (если нужен ManifestStaticFilesStorage)

Если в будущем понадобится ManifestStaticFilesStorage для версионирования статических файлов:

```bash
# На сервере
cd ~/ReplacementLog
source .venv/bin/activate
python manage.py collectstatic --clear --noinput
```

И изменить в `production.py`:
```python
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
```

## Проверка

Приложение должно работать без ошибок 500. Проверьте:
- Веб-интерфейс доступен
- Статические файлы загружаются (CSS, JS, изображения)
- Нет ошибок в логах





