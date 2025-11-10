# Быстрая настройка systemd service для автозапуска

## Выполните на сервере с правами sudo

```bash
ssh zero@10.45.20.40

# 1. Создаем файл сервиса
sudo nano /etc/systemd/system/replacementlog.service
```

Вставьте следующее содержимое:

```ini
[Unit]
Description=ReplacementLog Django Application
After=network.target postgresql.service

[Service]
Type=simple
User=zero
WorkingDirectory=/home/zero/ReplacementLog
Environment="PATH=/home/zero/ReplacementLog/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DJANGO_SETTINGS_MODULE=shift_log_project.settings"
EnvironmentFile=/home/zero/ReplacementLog/.env
ExecStart=/home/zero/ReplacementLog/.venv/bin/python3 /home/zero/ReplacementLog/manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10
StandardOutput=append:/var/log/replacementlog.log
StandardError=append:/var/log/replacementlog.log

[Install]
WantedBy=multi-user.target
```

Сохраните (Ctrl+O, Enter, Ctrl+X) и выполните:

```bash
# 2. Перезагружаем systemd
sudo systemctl daemon-reload

# 3. Включаем автозапуск
sudo systemctl enable replacementlog.service

# 4. Останавливаем текущий процесс (если запущен)
pkill -f 'manage.py runserver'

# 5. Запускаем через systemd
sudo systemctl start replacementlog.service

# 6. Проверяем статус
sudo systemctl status replacementlog.service
```

## Проверка работы

```bash
# Статус сервиса
sudo systemctl status replacementlog

# Логи
sudo journalctl -u replacementlog -f

# Или логи из файла
tail -f /var/log/replacementlog.log

# Проверка порта
netstat -tlnp | grep :8000
```

## Управление сервисом

```bash
# Запустить
sudo systemctl start replacementlog

# Остановить
sudo systemctl stop replacementlog

# Перезапустить
sudo systemctl restart replacementlog

# Статус
sudo systemctl status replacementlog

# Отключить автозапуск
sudo systemctl disable replacementlog
```

## После настройки

Приложение будет:
- ✅ Автоматически запускаться при перезагрузке сервера
- ✅ Автоматически перезапускаться при сбоях
- ✅ Работать в фоновом режиме
- ✅ Логироваться в `/var/log/replacementlog.log`

## Важно

Убедитесь, что файл `.env` существует и содержит все необходимые переменные:
```bash
cat ~/ReplacementLog/.env
```

Должно быть:
```
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
TELEGRAM_NOTIFICATIONS_ENABLED=True
```

