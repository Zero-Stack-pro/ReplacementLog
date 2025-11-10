# Настройка Telegram уведомлений

## 1. Установка токена бота

Установите переменную окружения `TELEGRAM_BOT_TOKEN`:

### Linux/macOS:
```bash
export TELEGRAM_BOT_TOKEN="8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"
```

### Для постоянной установки (добавьте в ~/.bashrc или ~/.zshrc):
```bash
echo 'export TELEGRAM_BOT_TOKEN="8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"' >> ~/.bashrc
source ~/.bashrc
```

### Windows (PowerShell):
```powershell
$env:TELEGRAM_BOT_TOKEN="8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"
```

### Windows (CMD):
```cmd
set TELEGRAM_BOT_TOKEN=8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ
```

### Для production (systemd service, docker-compose, etc.):
Добавьте в файл конфигурации вашего сервиса:
```
Environment="TELEGRAM_BOT_TOKEN=8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ"
```

## 2. Установка telegram_id для сотрудника

### Способ 1: Через management команду

```bash
python manage.py set_telegram_id NovichenkoEE 5233776312
```

### Способ 2: Через Django admin

1. Зайдите в админ-панель Django
2. Перейдите в раздел "Сотрудники" (Employees)
3. Найдите сотрудника NovichenkoEE
4. Откройте для редактирования
5. В поле "Telegram ID" введите: `5233776312`
6. Сохраните изменения

### Способ 3: Через Django shell

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from shift_log.models import Employee

user = User.objects.get(username='NovichenkoEE')
employee = Employee.objects.get(user=user)
employee.telegram_id = '5233776312'
employee.save()
print(f"Установлен telegram_id для {employee.get_full_name()}")
```

## 3. Проверка работы

После настройки токена и telegram_id, все уведомления, создаваемые через функцию `send_notification()`, будут автоматически дублироваться в Telegram.

Для проверки можно создать тестовое уведомление через Django shell:

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
    title='Тестовое уведомление',
    message='Это тестовое сообщение для проверки работы Telegram уведомлений'
)
```

## 4. Отключение Telegram уведомлений

Если нужно временно отключить отправку в Telegram (но сохранить создание уведомлений в БД):

```bash
export TELEGRAM_NOTIFICATIONS_ENABLED="False"
```

Или установите в settings.py:
```python
TELEGRAM_NOTIFICATIONS_ENABLED = False
```

## Важные замечания

- **Безопасность**: Токен бота является секретной информацией. Никогда не коммитьте его в git!
- **Telegram ID**: Это числовой идентификатор пользователя в Telegram. Его можно получить через бота @userinfobot или из API Telegram.
- **Проверка токена**: Убедитесь, что бот создан через @BotFather и токен действителен.

