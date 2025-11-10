# Настройка маршрутизации для двух сетевых интерфейсов

## Проблема
Трафик к Telegram API идет через интерфейс ens35 (10.45.20.40 - без интернета) вместо ens160 (192.168.97.124 - с интернетом).

## Решение

### Вариант 1: Настройка маршрутизации (рекомендуется)

На сервере выполните:

```bash
ssh zero@10.45.20.40

# Удалить маршрут по умолчанию через ens35 (если он мешает)
# Или изменить метрику, чтобы интернет шел через ens160

# Проверка текущих маршрутов
ip route show

# Настройка маршрута для внешних адресов через ens160
# Для Telegram API (149.154.167.0/24)
sudo ip route add 149.154.167.0/24 via 192.168.97.1 dev ens160

# Или для всех внешних адресов (кроме локальной сети)
sudo ip route add 0.0.0.0/1 via 192.168.97.1 dev ens160 metric 50
sudo ip route add 128.0.0.0/1 via 192.168.97.1 dev ens160 metric 50

# Для постоянной настройки добавьте в /etc/network/interfaces или netplan
```

### Вариант 2: Изменение метрики маршрутов

```bash
# Увеличить метрику для ens35, чтобы интернет шел через ens160
sudo nmcli connection modify 'Wired connection 1' ipv4.route-metric 200
sudo nmcli connection up 'Wired connection 1'
```

### Вариант 3: Использование привязки сокетов в коде (уже реализовано)

Код уже настроен для привязки к интерфейсу ens160 через `local_address` в httpx. Если это не работает стабильно, используйте варианты 1 или 2.

## Проверка

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
    title='Тест маршрутизации',
    message='Проверка работы через правильный интерфейс'
)
```

## Текущая конфигурация

- **ens35** (10.45.20.40): локальная сеть, статический IP, метрика 100
- **ens160** (192.168.97.124): интернет, DHCP, метрика 101

Проблема: маршрут через ens35 имеет меньшую метрику, поэтому трафик идет через него.

## Постоянное решение

Для постоянной настройки добавьте в конфигурацию сети (netplan или NetworkManager):

```yaml
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  ethernets:
    ens35:
      addresses:
        - 10.45.20.40/24
      routes:
        - to: 10.45.20.0/24
          via: 10.45.20.1
          metric: 100
    ens160:
      dhcp4: yes
      routes:
        - to: 0.0.0.0/0
          via: 192.168.97.1
          metric: 50
```

Затем:
```bash
sudo netplan apply
```

