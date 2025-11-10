# Исправление проблемы с DNS на сервере

## Проблема
Сервер не может разрешить DNS имя `api.telegram.org`, что приводит к ошибке:
```
httpx.ConnectError: [Errno -3] Temporary failure in name resolution
```

## Диагностика

Проверьте DNS:
```bash
ssh zero@10.45.20.40
ping api.telegram.org
nslookup api.telegram.org
```

Если не работает, проверьте статус systemd-resolved:
```bash
systemctl status systemd-resolved
resolvectl status
```

## Решение

### Вариант 1: Настройка DNS через systemd-resolved (рекомендуется)

```bash
sudo nano /etc/systemd/resolved.conf
```

Добавьте или раскомментируйте:
```ini
[Resolve]
DNS=8.8.8.8 8.8.4.4
FallbackDNS=1.1.1.1 1.0.0.1
```

Перезапустите:
```bash
sudo systemctl restart systemd-resolved
```

### Вариант 2: Настройка DNS через NetworkManager

```bash
sudo nmcli connection modify "имя_подключения" ipv4.dns "8.8.8.8 8.8.4.4"
sudo nmcli connection up "имя_подключения"
```

### Вариант 3: Временное решение через /etc/hosts

```bash
# Получите IP адрес api.telegram.org (можно через другой сервер или онлайн)
# Затем добавьте в /etc/hosts:
sudo echo "149.154.167.220 api.telegram.org" >> /etc/hosts
```

**Внимание:** IP адреса Telegram могут меняться, поэтому это временное решение.

### Вариант 4: Настройка через /etc/resolv.conf (если не используется systemd-resolved)

```bash
sudo nano /etc/resolv.conf
```

Добавьте:
```
nameserver 8.8.8.8
nameserver 8.8.4.4
```

**Внимание:** Если используется systemd-resolved, этот файл будет перезаписан.

## Проверка

После настройки проверьте:

```bash
# Проверка DNS
ping -c 2 api.telegram.org
nslookup api.telegram.org

# Проверка через Python
python3 -c "import socket; print(socket.gethostbyname('api.telegram.org'))"

# Проверка Telegram API
curl https://api.telegram.org/bot8391231295:AAE1UNo_b3IH1CB29ktSAYIM41s1dg8oFrQ/getMe
```

## После исправления DNS

Перезапустите Django приложение:

```bash
cd ~/ReplacementLog
pkill -f 'manage.py runserver'
source .venv/bin/activate
nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_runserver.log 2>&1 &
```

И проверьте отправку уведомлений.

## Альтернативное решение

Если DNS не удается настроить, можно использовать прокси или VPN для доступа к Telegram API, но это не рекомендуется для production.

