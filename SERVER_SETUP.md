# Настройка Telegram уведомлений на сервере

## Проблема: уведомления не приходят на сервере

Если уведомления перестали приходить после переноса на сервер, проверьте следующие пункты:

## 1. Проверка настроек

Запустите диагностическую команду:

```bash
python manage.py check_telegram
```

Эта команда покажет:
- Установлен ли токен бота
- Включены ли уведомления
- Подключение к боту
- Сотрудников с настроенным telegram_id
- Последние уведомления

## 2. Установка переменной окружения на сервере

### Вариант A: Systemd service

Если приложение запускается через systemd, добавьте переменную в файл сервиса:

```bash
sudo nano /etc/systemd/system/your-app.service
```

Добавьте в секцию `[Service]`:

```ini
[Service]
Environment="TELEGRAM_BOT_TOKEN=8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"
Environment="TELEGRAM_NOTIFICATIONS_ENABLED=True"
```

Перезагрузите сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl restart your-app
```

### Вариант B: Gunicorn

Если используете Gunicorn, создайте файл с переменными окружения:

```bash
nano /path/to/your/app/.env
```

Добавьте:
```
TELEGRAM_BOT_TOKEN=8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ
TELEGRAM_NOTIFICATIONS_ENABLED=True
```

Запустите Gunicorn с загрузкой переменных:

```bash
source /path/to/your/app/.env
gunicorn shift_log_project.wsgi:application
```

Или используйте `gunicorn --env TELEGRAM_BOT_TOKEN=ваш_токен ...`

### Вариант C: Supervisor

В конфигурации supervisor (`/etc/supervisor/conf.d/your-app.conf`):

```ini
[program:your-app]
environment=TELEGRAM_BOT_TOKEN="8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ",TELEGRAM_NOTIFICATIONS_ENABLED="True"
```

Перезагрузите:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart your-app
```

### Вариант D: Docker

В `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - TELEGRAM_BOT_TOKEN=8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ
      - TELEGRAM_NOTIFICATIONS_ENABLED=True
```

Или в `.env` файле:
```
TELEGRAM_BOT_TOKEN=8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ
TELEGRAM_NOTIFICATIONS_ENABLED=True
```

### Вариант E: Временная установка (для тестирования)

```bash
export TELEGRAM_BOT_TOKEN="8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"
export TELEGRAM_NOTIFICATIONS_ENABLED="True"
```

## 3. Проверка логов

Проверьте логи Django на наличие ошибок:

```bash
# Если используете systemd
sudo journalctl -u your-app -f

# Если логи в файле
tail -f /path/to/logs/django.log

# Или в настройках Django
python manage.py shell
>>> import logging
>>> logger = logging.getLogger('shift_log.services.telegram_service')
>>> logger.setLevel(logging.DEBUG)
```

## 4. Проверка доступа к Telegram API

Убедитесь, что сервер может обращаться к API Telegram:

```bash
curl https://api.telegram.org/bot8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ/getMe
```

Должен вернуться JSON с информацией о боте.

## 5. Проверка telegram_id сотрудников

Убедитесь, что telegram_id сохранены в базе данных:

```bash
python manage.py shell
```

```python
from shift_log.models import Employee
employees = Employee.objects.filter(telegram_id__isnull=False).exclude(telegram_id='')
for emp in employees:
    print(f"{emp.get_full_name()}: {emp.telegram_id}")
```

## 6. Тестовая отправка

После настройки переменных окружения и перезапуска сервиса:

```bash
python manage.py shell
```

```python
from shift_log.models import Employee
from shift_log.utils import send_notification

employee = Employee.objects.get(user__username='NovichenkoEE')
send_notification(
    recipient=employee,
    notification_type='task_assigned',
    title='Тест с сервера',
    message='Это тестовое сообщение с сервера для проверки работы'
)
```

## Частые проблемы

1. **Переменная окружения не установлена** - самая частая проблема
2. **Сервис не перезапущен** после установки переменной
3. **Блокировка файрволом** - сервер не может обратиться к api.telegram.org
4. **Неправильный токен** - проверьте токен через @BotFather
5. **Пользователь не начал диалог с ботом** - нужно отправить /start боту

## Быстрая диагностика

Выполните все команды по порядку:

```bash
# 1. Проверка настроек
python manage.py check_telegram

# 2. Проверка переменной окружения в текущей сессии
echo $TELEGRAM_BOT_TOKEN

# 3. Проверка доступа к API
curl -s https://api.telegram.org/bot8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ/getMe | python -m json.tool

# 4. Проверка логов (если есть)
tail -n 50 /path/to/logs/*.log | grep -i telegram
```

