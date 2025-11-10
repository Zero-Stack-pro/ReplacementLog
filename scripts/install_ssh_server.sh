#!/bin/bash
# Скрипт для установки и настройки SSH сервера на Ubuntu/Debian
# Выполнять на сервере с правами root или через sudo

set -e

echo "=========================================="
echo "Установка и настройка SSH сервера"
echo "=========================================="

# Определение дистрибутива
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Не удалось определить ОС"
    exit 1
fi

echo "Обнаружена ОС: $OS"

# Обновление пакетов
echo "Обновление списка пакетов..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get update
    apt-get install -y openssh-server
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    yum install -y openssh-server
else
    echo "Неподдерживаемая ОС. Установите openssh-server вручную."
    exit 1
fi

# Проверка статуса SSH
echo "Проверка статуса SSH сервера..."
if systemctl is-active --quiet sshd || systemctl is-active --quiet ssh; then
    echo "✓ SSH сервер уже запущен"
else
    echo "Запуск SSH сервера..."
    if systemctl list-units --type=service | grep -q "sshd.service"; then
        systemctl start sshd
        systemctl enable sshd
    elif systemctl list-units --type=service | grep -q "ssh.service"; then
        systemctl start ssh
        systemctl enable ssh
    else
        echo "Не удалось найти сервис SSH"
        exit 1
    fi
fi

# Резервная копия конфигурации
SSH_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSH_CONFIG" ]; then
    if [ ! -f "${SSH_CONFIG}.backup" ]; then
        echo "Создание резервной копии конфигурации..."
        cp "$SSH_CONFIG" "${SSH_CONFIG}.backup"
    fi
fi

# Настройка SSH (базовые параметры безопасности)
echo "Настройка SSH конфигурации..."
cat >> "$SSH_CONFIG" << 'EOF'

# Дополнительные настройки безопасности (добавлено скриптом)
# Разрешить аутентификацию по паролю (можно отключить после настройки ключей)
PasswordAuthentication yes

# Разрешить вход для root (можно отключить для безопасности)
PermitRootLogin yes

# Максимальное количество попыток входа
MaxAuthTries 6

# Таймаут для неактивных сессий (в секундах)
ClientAliveInterval 300
ClientAliveCountMax 2

# Отключить пустые пароли
PermitEmptyPasswords no
EOF

# Проверка порта SSH
SSH_PORT=$(grep -E "^Port" "$SSH_CONFIG" | awk '{print $2}' || echo "22")
echo "SSH работает на порту: $SSH_PORT"

# Проверка файрвола
echo "Проверка файрвола..."
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        echo "UFW активен. Открытие порта $SSH_PORT..."
        ufw allow "$SSH_PORT/tcp"
        echo "✓ Порт $SSH_PORT открыт в UFW"
    else
        echo "UFW не активен"
    fi
elif command -v firewall-cmd &> /dev/null; then
    if systemctl is-active --quiet firewalld; then
        echo "Firewalld активен. Открытие порта $SSH_PORT..."
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --reload
        echo "✓ SSH сервис открыт в firewalld"
    else
        echo "Firewalld не активен"
    fi
else
    echo "Файрвол не обнаружен или не настроен"
fi

# Перезапуск SSH сервера
echo "Перезапуск SSH сервера..."
if systemctl list-units --type=service | grep -q "sshd.service"; then
    systemctl restart sshd
elif systemctl list-units --type=service | grep -q "ssh.service"; then
    systemctl restart ssh
fi

# Проверка статуса
sleep 2
if systemctl is-active --quiet sshd || systemctl is-active --quiet ssh; then
    echo "✓ SSH сервер успешно запущен и работает"
else
    echo "✗ Ошибка: SSH сервер не запустился"
    exit 1
fi

# Вывод информации
echo ""
echo "=========================================="
echo "SSH сервер успешно установлен и настроен!"
echo "=========================================="
echo ""
echo "Информация о сервере:"
echo "  - IP адрес: $(hostname -I | awk '{print $1}')"
echo "  - Порт SSH: $SSH_PORT"
echo "  - Статус: $(systemctl is-active sshd 2>/dev/null || systemctl is-active ssh 2>/dev/null || echo 'неизвестно')"
echo ""
echo "Для подключения используйте:"
echo "  ssh username@$(hostname -I | awk '{print $1}')"
echo ""
echo "ВАЖНО: После настройки ключей рекомендуется:"
echo "  1. Отключить PasswordAuthentication"
echo "  2. Отключить PermitRootLogin"
echo "  3. Изменить стандартный порт (опционально)"
echo ""

