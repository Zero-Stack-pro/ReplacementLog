# Настройка systemd service для автоматического запуска

## Создание systemd service

Выполните на сервере с правами sudo:

```bash
ssh zero@10.45.20.40
cd ~/ReplacementLog
./scripts/create_systemd_service.sh
```

Или вручную:

```bash
sudo nano /etc/systemd/system/replacementlog.service
```

Добавьте следующее содержимое:

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
# Загружаем переменные окружения из .env файла
EnvironmentFile=/home/zero/ReplacementLog/.env
ExecStart=/home/zero/ReplacementLog/.venv/bin/python3 /home/zero/ReplacementLog/manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10
StandardOutput=append:/var/log/replacementlog.log
StandardError=append:/var/log/replacementlog.log

[Install]
WantedBy=multi-user.target
```

Затем:

```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable replacementlog.service

# Запускаем сервис
sudo systemctl start replacementlog.service

# Проверяем статус
sudo systemctl status replacementlog.service
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

# Просмотр логов
sudo journalctl -u replacementlog -f

# Или логи из файла
tail -f /var/log/replacementlog.log
```

## Проверка работы

После запуска проверьте:

```bash
# Проверка статуса
sudo systemctl status replacementlog

# Проверка порта
netstat -tlnp | grep :8000

# Проверка логов
sudo journalctl -u replacementlog -n 50
```

## Важно

1. **Файл .env должен существовать** и содержать все необходимые переменные окружения
2. **Права доступа:** Убедитесь, что пользователь `zero` имеет права на чтение `.env` файла
3. **Логи:** Логи сохраняются в `/var/log/replacementlog.log`
4. **Автозапуск:** Сервис будет автоматически запускаться при перезагрузке сервера

## Устранение проблем

Если сервис не запускается:

```bash
# Проверка логов
sudo journalctl -u replacementlog -n 100

# Проверка прав на файлы
ls -la /home/zero/ReplacementLog/.env
ls -la /home/zero/ReplacementLog/manage.py

# Проверка виртуального окружения
ls -la /home/zero/ReplacementLog/.venv/bin/python3
```

## Альтернатива: использование Gunicorn (для production)

Для production рекомендуется использовать Gunicorn вместо runserver:

```ini
[Service]
ExecStart=/home/zero/ReplacementLog/.venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    shift_log_project.wsgi:application
```

