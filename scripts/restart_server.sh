#!/bin/bash
# Скрипт для перезапуска Django приложения на сервере
# Загружает переменные окружения из .env файла

set -e

SERVER_IP="10.45.20.40"
SERVER_USER="zero"
PROJECT_DIR="~/ReplacementLog"

echo "Перезапуск Django приложения на сервере..."

# Находим процесс runserver
PID=$(ssh $SERVER_USER@$SERVER_IP "ps aux | grep 'manage.py runserver' | grep -v grep | awk '{print \$2}' | head -1" || echo "")

if [ -n "$PID" ]; then
    echo "Остановка текущего процесса (PID: $PID)..."
    ssh $SERVER_USER@$SERVER_IP "kill $PID" || echo "Процесс уже остановлен"
    sleep 2
fi

# Запуск с загрузкой .env
echo "Запуск приложения с переменными из .env..."
ssh $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && source .venv/bin/activate && nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &"

sleep 3

# Проверка статуса
if ssh $SERVER_USER@$SERVER_IP "ps aux | grep 'manage.py runserver' | grep -v grep" > /dev/null; then
    echo "✓ Приложение успешно запущено"
    echo "Проверка переменных окружения..."
    ssh $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && source .venv/bin/activate && python3 manage.py shell -c \"from django.conf import settings; print('TELEGRAM_BOT_TOKEN:', 'установлен' if getattr(settings, 'TELEGRAM_BOT_TOKEN', None) else 'НЕ установлен')\""
else
    echo "✗ Ошибка при запуске приложения"
    exit 1
fi

