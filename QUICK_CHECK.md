# Быстрая проверка Telegram на сервере

## Способ 1: Через Django shell (самый простой)

Выполните на сервере:

```bash
python manage.py shell
```

Затем вставьте и выполните этот код:

```python
import os
from django.conf import settings
from shift_log.models import Employee
from shift_log.services.telegram_service import TelegramService
import asyncio

# Проверка токена
token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
if token:
    print(f'✓ Токен установлен: {token[:10]}...{token[-10:]}')
else:
    print('✗ Токен НЕ установлен!')
    print('  Нужно установить: export TELEGRAM_BOT_TOKEN="8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"')

# Проверка бота
bot = TelegramService.get_bot()
if bot:
    try:
        async def get_bot_info():
            return await bot.get_me()
        bot_info = asyncio.run(get_bot_info())
        print(f'✓ Бот работает: @{bot_info.username}')
    except Exception as e:
        print(f'✗ Ошибка бота: {e}')
else:
    print('✗ Бот не создан (проверьте токен)')

# Проверка сотрудников
employees = Employee.objects.filter(telegram_id__isnull=False).exclude(telegram_id='')
print(f'\nСотрудников с telegram_id: {employees.count()}')
for emp in employees:
    print(f'  - {emp.get_full_name()}: {emp.telegram_id}')
```

## Способ 2: Через скрипт

Скопируйте файл `check_telegram_shell.py` на сервер и выполните:

```bash
python manage.py shell < check_telegram_shell.py
```

Или:

```bash
python check_telegram_shell.py
```

## Способ 3: Простая проверка переменной окружения

```bash
# Проверка переменной
echo $TELEGRAM_BOT_TOKEN

# Если пусто, установите:
export TELEGRAM_BOT_TOKEN="8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"

# Проверьте снова
echo $TELEGRAM_BOT_TOKEN
```

## Способ 4: Проверка через Python напрямую

```bash
python -c "
import os
token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
if token:
    print(f'Токен установлен: {token[:10]}...{token[-10:]}')
else:
    print('Токен НЕ установлен!')
"
```

## Что делать если токен не установлен

### Если используете systemd:

```bash
sudo nano /etc/systemd/system/your-app.service
```

Добавьте в `[Service]`:
```ini
Environment="TELEGRAM_BOT_TOKEN=8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl restart your-app
```

### Если используете Gunicorn/Supervisor:

Добавьте переменную в конфигурацию вашего сервиса или в файл `.env`.

### Временная установка (для теста):

```bash
export TELEGRAM_BOT_TOKEN="8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"
# Затем перезапустите приложение
```

## Тестовая отправка после настройки

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
    message='Проверка работы Telegram уведомлений'
)
print('Отправлено!')
```

