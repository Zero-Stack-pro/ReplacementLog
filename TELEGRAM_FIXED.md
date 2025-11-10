# Исправление проблемы с Telegram уведомлениями на сервере

## Проблема
Telegram уведомления не приходили на сервере, хотя на локальной машине работали.

## Причины
1. **Переменные окружения не были установлены** - `TELEGRAM_BOT_TOKEN` не был доступен при запуске приложения
2. **Ошибка с event loop** - проблема с обработкой asyncio в `telegram_service.py`

## Решение

### 1. Создан файл `.env` на сервере

Файл `/home/zero/ReplacementLog/.env` содержит:
```
TELEGRAM_BOT_TOKEN=8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ
TELEGRAM_NOTIFICATIONS_ENABLED=True
```

### 2. Обновлен `settings.py` для автоматической загрузки `.env`

Добавлена загрузка переменных окружения из `.env` файла:
```python
# Загрузка переменных окружения из .env файла
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv не установлен, используем только переменные окружения системы
    pass
```

### 3. Исправлен `telegram_service.py`

Исправлена проблема с event loop для корректной работы в разных контекстах (Django shell, views, management commands).

### 4. Установлен `python-dotenv`

Добавлен в `requirements.txt` и установлен на сервере для автоматической загрузки `.env` файла.

## Проверка работы

### Тестовая отправка уведомления:

```bash
# На сервере
cd ~/ReplacementLog
source .venv/bin/activate
python3 manage.py shell
```

```python
from shift_log.models import Employee
from shift_log.utils import send_notification

employee = Employee.objects.filter(telegram_id__isnull=False).exclude(telegram_id='').first()
send_notification(
    recipient=employee,
    notification_type='task_assigned',
    title='Тест с сервера',
    message='Проверка работы Telegram уведомлений'
)
```

### Проверка настроек:

```bash
python3 manage.py shell
```

```python
from django.conf import settings
print('TELEGRAM_BOT_TOKEN:', 'установлен' if getattr(settings, 'TELEGRAM_BOT_TOKEN', None) else 'НЕ установлен')
print('TELEGRAM_NOTIFICATIONS_ENABLED:', getattr(settings, 'TELEGRAM_NOTIFICATIONS_ENABLED', False))
```

## Текущий статус

✅ **Telegram уведомления работают на сервере**
✅ **Переменные окружения загружаются автоматически из `.env`**
✅ **Проблема с event loop исправлена**
✅ **Тестовые уведомления успешно отправляются**

## Важно

1. **Файл `.env` должен быть в `.gitignore`** - не коммитить токены в репозиторий
2. **При перезапуске приложения** переменные загружаются автоматически из `.env`
3. **Для production** рекомендуется использовать systemd service с переменными окружения

## Перезапуск приложения

После изменения `.env` файла или кода, перезапустите приложение:

```bash
# На сервере
cd ~/ReplacementLog
source .venv/bin/activate

# Остановить текущий процесс
pkill -f "manage.py runserver"

# Запустить заново (переменные загрузятся из .env автоматически)
nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
```

Или используйте скрипт:
```bash
./scripts/restart_server.sh
```

## Сотрудники с настроенным Telegram

- **Евгений Новиченко** (NovichenkoEE): telegram_id = 5233776312

## Дополнительная информация

- Бот: @replacementlog_bot
- Токен: 8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ
- Сервер: 10.45.20.40
- Проект: /home/zero/ReplacementLog

