#!/bin/bash
# Скрипт для обновления systemd service для production с Gunicorn

set -e

SERVICE_NAME="replacementlog"
PROJECT_DIR="/home/zero/ReplacementLog"
USER="zero"
VENV_PATH="$PROJECT_DIR/.venv"
GUNICORN_PATH="$VENV_PATH/bin/gunicorn"
CONFIG_FILE="$PROJECT_DIR/gunicorn_config.py"

echo "Обновление systemd service для production с Gunicorn..."

# Создаем файл сервиса
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=ReplacementLog Django Application (Gunicorn)
After=network.target postgresql.service

[Service]
Type=notify
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DJANGO_SETTINGS_MODULE=shift_log_project.settings"
Environment="DJANGO_ENVIRONMENT=production"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$GUNICORN_PATH --config $CONFIG_FILE shift_log_project.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10
StandardOutput=append:/var/log/${SERVICE_NAME}.log
StandardError=append:/var/log/${SERVICE_NAME}.log

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Файл сервиса обновлен: $SERVICE_FILE"

# Перезагружаем systemd
sudo systemctl daemon-reload

echo "✓ systemd перезагружен"

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














