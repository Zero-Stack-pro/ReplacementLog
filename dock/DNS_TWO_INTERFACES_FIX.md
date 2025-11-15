# Исправление DNS при двух сетевых интерфейсах

## Ситуация
- **ens35** (10.45.20.40) - статический IP для локальной сети
- **ens160** (192.168.97.124) - DHCP для интернета

Проблема: DNS запросы идут через ens160, который использует локальные DNS серверы (192.168.95.11, 192.168.95.12), не могущие разрешить внешние домены типа `api.telegram.org`.

## Решение

### Вариант 1: Настройка DNS через NetworkManager (рекомендуется)

```bash
ssh zero@10.45.20.40

# Настройка DNS для интернет интерфейса (ens160)
sudo nmcli connection modify 'netplan-ens160' ipv4.dns "8.8.8.8 8.8.4.4"
sudo nmcli connection modify 'netplan-ens160' ipv4.ignore-auto-dns no
sudo nmcli connection up 'netplan-ens160'

# Перезапуск systemd-resolved
sudo systemctl restart systemd-resolved
```

### Вариант 2: Настройка через systemd-resolved

```bash
sudo nano /etc/systemd/resolved.conf
```

Добавьте:
```ini
[Resolve]
DNS=8.8.8.8 8.8.4.4
FallbackDNS=1.1.1.1 1.0.0.1
```

```bash
sudo systemctl restart systemd-resolved
```

### Вариант 3: Настройка через netplan (если используется)

```bash
sudo nano /etc/netplan/01-netcfg.yaml
```

Добавьте DNS для интерфейса с интернетом:
```yaml
network:
  version: 2
  ethernets:
    ens160:
      dhcp4: yes
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
    ens35:
      addresses:
        - 10.45.20.40/24
      gateway4: 10.45.20.1
```

```bash
sudo netplan apply
```

## Проверка

```bash
# Проверка DNS серверов
resolvectl status

# Проверка разрешения имени
ping -c 2 api.telegram.org
nslookup api.telegram.org

# Проверка через Python
python3 -c "import socket; print(socket.gethostbyname('api.telegram.org'))"
```

## После исправления DNS

Перезапустите Django приложение:

```bash
cd ~/ReplacementLog
pkill -f 'manage.py runserver'
source .venv/bin/activate
nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_runserver.log 2>&1 &
```

## Текущая конфигурация

- **ens35** (10.45.20.40): локальная сеть, статический IP
- **ens160** (192.168.97.124): интернет, DHCP
- **DNS на ens160**: 192.168.95.11, 192.168.95.12 (локальные, не разрешают внешние домены)

## Важно

После настройки DNS для ens160, убедитесь, что:
1. Локальные DNS запросы (для внутренних сервисов) все еще работают
2. Внешние DNS запросы идут через публичные DNS (8.8.8.8, 1.1.1.1)
3. Маршрутизация настроена правильно (интернет через ens160, локальная сеть через ens35)

