# Быстрое исправление DNS на сервере

## Проблема
DNS запросы идут через локальные DNS серверы (192.168.95.11, 192.168.95.12), которые не могут разрешить `api.telegram.org`.

## Решение (выполните на сервере с sudo)

```bash
ssh zero@10.45.20.40

# Вариант 1: Добавить публичные DNS к интерфейсу ens160 (рекомендуется)
sudo nmcli connection modify 'netplan-ens160' ipv4.dns "8.8.8.8 8.8.4.4 192.168.95.11 192.168.95.12"
sudo nmcli connection up 'netplan-ens160'
sudo systemctl restart systemd-resolved

# Или Вариант 2: Настроить глобальные DNS через systemd-resolved
sudo nano /etc/systemd/resolved.conf
```

В файле `/etc/systemd/resolved.conf` найдите `[Resolve]` и добавьте:
```ini
[Resolve]
DNS=8.8.8.8 8.8.4.4
FallbackDNS=192.168.95.11 192.168.95.12
```

Затем:
```bash
sudo systemctl restart systemd-resolved
```

## Проверка

```bash
# Проверка DNS
ping -c 2 api.telegram.org

# Если работает, перезапустите Django
cd ~/ReplacementLog
pkill -f 'manage.py runserver'
source .venv/bin/activate
nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_runserver.log 2>&1 &
```

## После исправления

Проверьте отправку уведомления через веб-интерфейс - оно должно прийти в Telegram!

