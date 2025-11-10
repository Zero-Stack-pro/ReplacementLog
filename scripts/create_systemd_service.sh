#!/bin/bash
# Скрипт для создания systemd service для Django приложения
# Выполнять на сервере с правами sudo

set -e

SERVICE_NAME="replacementlog"
PROJECT_DIR="/home/zero/ReplacementLog"
USER="zero"
VENV_PATH="$PROJECT_DIR/.venv"
PYTHON_PATH="$VENV_PATH/bin/python3"
MANAGE_PY="$PROJECT_DIR/manage.py"

echo "Создание systemd service для ReplacementLog..."

# Создаем файл сервиса
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=ReplacementLog Django Application
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DJANGO_SETTINGS_MODULE=shift_log_project.settings"
# Загружаем переменные окружения из .env файла
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PYTHON_PATH $MANAGE_PY runserver 0.0.0.0:8000
Restart=always
RestartSec=10
StandardOutput=append:/var/log/${SERVICE_NAME}.log
StandardError=append:/var/log/${SERVICE_NAME}.log

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Файл сервиса создан: $SERVICE_FILE"

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable ${SERVICE_NAME}.service

echo "✓ Сервис включен для автозапуска"

# Показываем статус
echo ""
echo "Текущий статус:"
sudo systemctl status ${SERVICE_NAME}.service --no-pager || echo "Сервис еще не запущен"

echo ""
echo "Для управления сервисом используйте:"
echo "  sudo systemctl start ${SERVICE_NAME}    # Запустить"
echo "  sudo systemctl stop ${SERVICE_NAME}     # Остановить"
echo "  sudo systemctl restart ${SERVICE_NAME}   # Перезапустить"
echo "  sudo systemctl status ${SERVICE_NAME}    # Статус"
echo "  sudo journalctl -u ${SERVICE_NAME} -f    # Логи"

