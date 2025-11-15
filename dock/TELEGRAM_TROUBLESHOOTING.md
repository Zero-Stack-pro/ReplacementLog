# Устранение проблем с Telegram уведомлениями

## Проблема: уведомления не приходят в Telegram

### Симптомы
- Уведомления создаются в базе данных
- Но не все уведомления приходят в Telegram
- После перезапуска сервера уведомления начинают работать

### Причины

1. **Переменные окружения не загружены**
   - `TELEGRAM_BOT_TOKEN` не установлен в окружении запущенного процесса
   - Runserver был запущен до обновления `settings.py` с загрузкой `.env`

2. **Код не обновлен**
   - Изменения в `utils.py` или `telegram_service.py` не применены
   - Нужен перезапуск runserver

### Решение

#### 1. Убедитесь, что `.env` файл существует на сервере

```bash
ssh zero@10.45.20.40
cd ~/ReplacementLog
cat .env
```

Должно быть:
```
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
TELEGRAM_NOTIFICATIONS_ENABLED=True
```

#### 2. Перезапустите runserver

```bash
# На сервере
cd ~/ReplacementLog
pkill -f 'manage.py runserver'
source .venv/bin/activate
nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_runserver.log 2>&1 &
```

Или используйте скрипт:
```bash
./scripts/restart_server.sh
```

#### 3. Проверьте, что переменные загружаются

```bash
ssh zero@10.45.20.40
cd ~/ReplacementLog
source .venv/bin/activate
python3 manage.py shell
```

```python
from django.conf import settings
import os

# Проверка переменных
print('TELEGRAM_BOT_TOKEN в os.environ:', 'установлен' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'НЕ установлен')
print('TELEGRAM_BOT_TOKEN в settings:', 'установлен' if getattr(settings, 'TELEGRAM_BOT_TOKEN', None) else 'НЕ установлен')
```

#### 4. Проверьте логи на наличие ошибок

```bash
ssh zero@10.45.20.40
tail -f /tmp/django_runserver.log | grep -iE '(telegram|error|exception)'
```

#### 5. Тестовая отправка

```bash
ssh zero@10.45.20.40
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
    title='Тест',
    message='Проверка работы Telegram уведомлений'
)
```

### Проверка работы уведомлений

#### Проверка последних уведомлений в БД

```python
from shift_log.models import Notification
from django.utils import timezone
from datetime import timedelta

recent = Notification.objects.filter(
    sent_at__gte=timezone.now() - timedelta(minutes=10)
).order_by('-sent_at')

for notif in recent:
    print(f'{notif.id}: {notif.title} → {notif.recipient.get_full_name()} (telegram_id: {notif.recipient.telegram_id})')
```

#### Проверка логов отправки

В коде добавлено детальное логирование:
- `INFO`: Попытка отправки Telegram уведомления
- `INFO`: ✓ Telegram уведомление успешно отправлено
- `WARNING`: ✗ Telegram уведомление не отправлено (вернуло False)
- `ERROR`: Error sending Telegram notification

### Автоматическая проверка

Используйте скрипт для проверки:

```bash
./scripts/connect_to_server.sh "cd ~/ReplacementLog && source .venv/bin/activate && python3 manage.py shell << 'EOF'
from django.conf import settings
from shift_log.models import Employee
from shift_log.services.telegram_service import TelegramService

print('=== Проверка настроек Telegram ===\n')

token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
print(f'TELEGRAM_BOT_TOKEN: {\"установлен\" if token else \"НЕ установлен\"}')

bot = TelegramService.get_bot()
print(f'Бот создан: {\"да\" if bot else \"нет\"}')

employees = Employee.objects.filter(telegram_id__isnull=False).exclude(telegram_id='')
print(f'Сотрудников с telegram_id: {employees.count()}')
EOF
"
```

### Важные моменты

1. **После изменения `.env` или кода** - обязательно перезапустите runserver
2. **Проверяйте логи** - там могут быть ошибки, которые не видны в интерфейсе
3. **Убедитесь, что у сотрудника указан telegram_id** - без него уведомления не отправляются
4. **Проверьте, что бот работает** - используйте `TelegramService.get_bot()` для проверки

### Частые проблемы

1. **Уведомления создаются, но не отправляются**
   - Проверьте логи на ошибки
   - Убедитесь, что `TELEGRAM_BOT_TOKEN` установлен
   - Проверьте, что у сотрудника указан `telegram_id`

2. **После перезапуска работает, потом перестает**
   - Возможно, runserver был перезапущен без загрузки `.env`
   - Проверьте, что `settings.py` загружает `.env` файл

3. **Только некоторые уведомления приходят**
   - Проверьте логи - возможно, есть ошибки при отправке
   - Убедитесь, что все сотрудники имеют `telegram_id`

### Контакты для проверки

- **Евгений Новиченко** (NovichenkoEE): telegram_id = 5233776312 ✅
- Другие сотрудники: проверьте наличие telegram_id в базе данных

