# Исправление проблем с таймаутами Telegram API

## Проблема
Telegram уведомления иногда не отправляются из-за ошибок таймаута API Telegram.

## Решение

### Что сделано в коде:

1. **Увеличены таймауты HTTP клиента:**
   - Подключение: 15 секунд
   - Чтение: 30 секунд
   - Запись: 15 секунд
   - Пул соединений: 15 секунд

2. **Добавлена retry логика:**
   - До 3 попыток отправки
   - Экспоненциальная задержка между попытками (1, 2, 4 секунды)
   - Автоматический retry при ошибках timeout, connection, network

3. **Увеличен таймаут ThreadPoolExecutor:**
   - С 10 до 60 секунд (с учетом retry)

### Настройка маршрутизации на сервере (важно!)

Для стабильной работы нужно настроить маршрутизацию, чтобы трафик к Telegram API шел через интерфейс с интернетом (ens160):

```bash
ssh zero@10.45.20.40

# Настройка маршрута для Telegram API через интерфейс с интернетом
sudo ip route add 149.154.167.0/24 via 192.168.97.1 dev ens160

# Или для всех внешних адресов (кроме локальной сети)
sudo ip route add 0.0.0.0/1 via 192.168.97.1 dev ens160 metric 50
sudo ip route add 128.0.0.0/1 via 192.168.97.1 dev ens160 metric 50

# Для постоянной настройки измените метрику интерфейса
sudo nmcli connection modify 'Wired connection 1' ipv4.route-metric 200
sudo nmcli connection up 'Wired connection 1'
```

### Проверка

После настройки проверьте:

```bash
# Проверка маршрута к Telegram API
ip route get 149.154.167.220

# Должно быть: через ens160 (192.168.97.1)

# Проверка отправки уведомления
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
    title='Тест с retry',
    message='Проверка работы с retry логикой и увеличенными таймаутами'
)
```

### Логирование

Теперь в логах вы увидите:
- Предупреждения о повторных попытках
- Информацию о задержках между попытками
- Детальные ошибки при неудачных попытках

Проверьте логи:
```bash
tail -f /tmp/django_runserver.log | grep -i telegram
```

## Текущая конфигурация

- **Таймауты:** увеличены до 15-30 секунд
- **Retry:** до 3 попыток с экспоненциальной задержкой
- **ThreadPoolExecutor timeout:** 60 секунд

## Важно

1. Настройте маршрутизацию на сервере для стабильной работы
2. Проверьте, что DNS настроен правильно (см. DNS_FIX.md)
3. Убедитесь, что интерфейс ens160 имеет доступ к интернету

