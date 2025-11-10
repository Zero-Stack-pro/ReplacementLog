#!/bin/bash
# Скрипт для настройки systemd service
# Выполнять на сервере с правами sudo

echo "Настройка systemd service для ReplacementLog..."

# Копируем файл сервиса
sudo cp ~/replacementlog.service /etc/systemd/system/replacementlog.service

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable replacementlog.service

# Останавливаем текущий процесс (если запущен)
pkill -f 'manage.py runserver' || true
sleep 2

# Запускаем через systemd
sudo systemctl start replacementlog.service

# Ждем немного
sleep 3

# Показываем статус
echo ""
echo "=== Статус сервиса ==="
sudo systemctl status replacementlog.service --no-pager | head -15

echo ""
echo "=== Полезные команды ==="
echo "  sudo systemctl start replacementlog    # Запустить"
echo "  sudo systemctl stop replacementlog     # Остановить"
echo "  sudo systemctl restart replacementlog  # Перезапустить"
echo "  sudo systemctl status replacementlog    # Статус"
echo "  sudo journalctl -u replacementlog -f   # Логи"

