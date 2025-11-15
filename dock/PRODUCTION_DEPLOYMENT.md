# Production Deployment Guide

## ✅ Что настроено

### 1. Модульная структура настроек
- `settings/base.py` - базовые настройки для всех окружений
- `settings/development.py` - настройки для разработки (DEBUG=True)
- `settings/production.py` - настройки для production (DEBUG=False, безопасность, оптимизации)

### 2. Gunicorn WSGI сервер
- Production-ready WSGI сервер вместо `runserver`
- Настроено количество воркеров: `(2 x CPU cores) + 1`
- Threading: 2 потока на воркер
- Таймауты и лимиты запросов для предотвращения утечек памяти
- Логирование в `/var/log/replacementlog-access.log` и `/var/log/replacementlog-error.log`

### 3. Production настройки
- ✅ `DEBUG = False`
- ✅ Безопасные заголовки (XSS, Content-Type, Frame Options)
- ✅ Connection pooling для базы данных (CONN_MAX_AGE=600)
- ✅ Кэширование (Redis или локальный кэш)
- ✅ Оптимизированное логирование с ротацией
- ✅ Оптимизация статических файлов

### 4. Systemd Service
- Автоматический запуск при перезагрузке
- Автоматический перезапуск при сбоях
- Управление через systemd

## Текущая конфигурация

### Gunicorn
- **Workers**: Автоматически определяется как `(2 x CPU cores) + 1`
- **Threads**: 2 на воркер
- **Timeout**: 120 секунд
- **Max requests**: 1000 (с jitter 100) для предотвращения утечек памяти
- **Preload app**: Да (экономия памяти)

### База данных
- **Connection pooling**: 600 секунд
- **PostgreSQL**: Оптимизированные настройки подключения

### Кэширование
- Redis (если доступен) или локальный кэш
- Timeout: 300 секунд

## Управление сервисом

```bash
# Статус
sudo systemctl status replacementlog

# Запустить
sudo systemctl start replacementlog

# Остановить
sudo systemctl stop replacementlog

# Перезапустить
sudo systemctl restart replacementlog

# Логи
sudo journalctl -u replacementlog -f

# Логи Gunicorn
tail -f /var/log/replacementlog-access.log
tail -f /var/log/replacementlog-error.log

# Логи Django
tail -f /var/log/replacementlog-django.log
tail -f /var/log/replacementlog-django-error.log
```

## Мониторинг производительности

```bash
# Использование ресурсов
ps aux | grep gunicorn
top -p $(pgrep -d, -f gunicorn)

# Количество соединений
netstat -an | grep :8000 | wc -l

# Проверка воркеров
ps aux | grep gunicorn | grep -v grep | wc -l
```

## Переменные окружения

В `.env` файле должны быть:
```bash
DJANGO_ENVIRONMENT=production
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_NOTIFICATIONS_ENABLED=True
SECRET_KEY=your_secret_key_here
DB_NAME=ReplacementLog
DB_USER=zero
DB_PASSWORD=your_password
DB_HOST=10.45.20.40
DB_PORT=5432
```

## Оптимизация производительности

### Текущие настройки
- Connection pooling для БД
- Кэширование запросов
- Оптимизация статических файлов
- Preload приложения в Gunicorn

### Дополнительные оптимизации (опционально)

1. **Nginx как reverse proxy** (рекомендуется):
   ```nginx
   upstream replacementlog {
       server 127.0.0.1:8000;
   }
   
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://replacementlog;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static/ {
           alias /home/zero/ReplacementLog/staticfiles/;
       }
       
       location /media/ {
           alias /home/zero/ReplacementLog/media/;
       }
   }
   ```

2. **Redis для кэширования** (если еще не установлен):
   ```bash
   sudo apt install redis-server
   sudo systemctl enable redis-server
   sudo systemctl start redis-server
   ```

3. **Мониторинг** (опционально):
   - Prometheus + Grafana
   - Sentry для отслеживания ошибок

## Безопасность

✅ Настроено:
- DEBUG = False
- Безопасные заголовки
- ALLOWED_HOSTS ограничен
- SECRET_KEY из переменных окружения

⚠️ Рекомендуется добавить (если используете HTTPS):
- SECURE_SSL_REDIRECT = True
- SESSION_COOKIE_SECURE = True
- CSRF_COOKIE_SECURE = True
- SECURE_HSTS_SECONDS = 31536000

## Обновление приложения

```bash
ssh zero@10.45.20.40
cd ~/ReplacementLog

# Обновить код
git pull origin main

# Обновить зависимости (если нужно)
source .venv/bin/activate
pip install -r requirements.txt

# Собрать статические файлы
python manage.py collectstatic --noinput

# Применить миграции (если есть)
python manage.py migrate

# Перезапустить сервис
sudo systemctl restart replacementlog
```

## Проверка работы

```bash
# Проверка статуса
sudo systemctl status replacementlog

# Проверка порта
netstat -tlnp | grep :8000

# Тестовая отправка уведомления
cd ~/ReplacementLog
source .venv/bin/activate
python manage.py shell
```

```python
from shift_log.models import Employee
from shift_log.utils import send_notification

employee = Employee.objects.filter(telegram_id__isnull=False).first()
send_notification(
    recipient=employee,
    notification_type='task_assigned',
    title='Тест production',
    message='Проверка работы в production режиме'
)
```

## Troubleshooting

### Проблема: Сервис не запускается
```bash
# Проверить логи
sudo journalctl -u replacementlog -n 50

# Проверить конфигурацию
sudo systemctl status replacementlog
```

### Проблема: Высокое использование памяти
```bash
# Уменьшить количество воркеров в gunicorn_config.py
workers = 2  # вместо автоматического определения
```

### Проблема: Медленные запросы
```bash
# Проверить логи
tail -f /var/log/replacementlog-error.log

# Проверить базу данных
psql -U zero -d ReplacementLog -c "SELECT * FROM pg_stat_activity;"
```

## Производительность

Ожидаемые улучшения после перехода на Gunicorn:
- ✅ Снижение использования CPU на 30-50%
- ✅ Снижение использования памяти на 20-40%
- ✅ Улучшение производительности под нагрузкой
- ✅ Лучшая обработка множественных запросов
- ✅ Автоматический перезапуск воркеров для предотвращения утечек памяти

