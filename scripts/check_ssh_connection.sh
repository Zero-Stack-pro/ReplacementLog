#!/bin/bash
# Скрипт для проверки SSH подключения к серверу
# Выполнять на локальной машине

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Параметры по умолчанию
SERVER_IP="${1:-10.45.20.40}"
SERVER_USER="${2:-zero}"
SSH_PORT="${3:-22}"

echo "=========================================="
echo "Проверка SSH подключения к серверу"
echo "=========================================="
echo "Сервер: $SERVER_USER@$SERVER_IP:$SSH_PORT"
echo ""

# Проверка наличия SSH клиента
if ! command -v ssh &> /dev/null; then
    echo -e "${RED}✗ SSH клиент не установлен${NC}"
    echo "Установите openssh-client:"
    echo "  Ubuntu/Debian: sudo apt-get install openssh-client"
    echo "  CentOS/RHEL: sudo yum install openssh-clients"
    exit 1
fi

echo -e "${GREEN}✓ SSH клиент установлен${NC}"

# Проверка доступности сервера (ping)
echo ""
echo "1. Проверка доступности сервера (ping)..."
if ping -c 1 -W 2 "$SERVER_IP" &> /dev/null; then
    echo -e "${GREEN}✓ Сервер доступен (ping успешен)${NC}"
else
    echo -e "${YELLOW}⚠ Сервер не отвечает на ping (может быть отключен ICMP)${NC}"
    echo "   Продолжаем проверку SSH..."
fi

# Проверка открытости порта SSH
echo ""
echo "2. Проверка открытости порта SSH ($SSH_PORT)..."
if command -v nc &> /dev/null; then
    if nc -z -w 3 "$SERVER_IP" "$SSH_PORT" 2>/dev/null; then
        echo -e "${GREEN}✓ Порт $SSH_PORT открыт и доступен${NC}"
    else
        echo -e "${RED}✗ Порт $SSH_PORT недоступен${NC}"
        echo "   Возможные причины:"
        echo "   - SSH сервер не запущен на сервере"
        echo "   - Файрвол блокирует порт"
        echo "   - Неправильный IP адрес"
        exit 1
    fi
elif command -v telnet &> /dev/null; then
    if timeout 3 telnet "$SERVER_IP" "$SSH_PORT" 2>/dev/null | grep -q "Connected"; then
        echo -e "${GREEN}✓ Порт $SSH_PORT открыт и доступен${NC}"
    else
        echo -e "${RED}✗ Порт $SSH_PORT недоступен${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Не удалось проверить порт (установите nc или telnet)${NC}"
fi

# Проверка SSH версии
echo ""
echo "3. Проверка версии SSH сервера..."
SSH_VERSION=$(ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -p "$SSH_PORT" "$SERVER_USER@$SERVER_IP" "echo 'SSH_OK'" 2>&1 | head -1)
if echo "$SSH_VERSION" | grep -q "SSH_OK"; then
    echo -e "${GREEN}✓ SSH подключение успешно!${NC}"
    SSH_SERVER_VERSION=$(ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -p "$SSH_PORT" "$SERVER_USER@$SERVER_IP" "sshd -V 2>&1" 2>/dev/null || echo "версия неизвестна")
    echo "   Версия SSH сервера: $SSH_SERVER_VERSION"
else
    # Попытка получить информацию о SSH сервере через ssh-keyscan
    if command -v ssh-keyscan &> /dev/null; then
        SSH_INFO=$(ssh-keyscan -p "$SSH_PORT" "$SERVER_IP" 2>&1 | head -1)
        if [ -n "$SSH_INFO" ] && ! echo "$SSH_INFO" | grep -q "ERROR"; then
            echo -e "${GREEN}✓ SSH сервер отвечает${NC}"
            echo "   Информация: $SSH_INFO"
        else
            echo -e "${RED}✗ Не удалось подключиться к SSH серверу${NC}"
            echo "   Ошибка: $SSH_VERSION"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠ Не удалось проверить SSH версию${NC}"
        echo "   Ответ сервера: $SSH_VERSION"
    fi
fi

# Проверка аутентификации (если есть ключи)
echo ""
echo "4. Проверка SSH ключей..."
if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ] || [ -f ~/.ssh/id_ecdsa ]; then
    echo -e "${GREEN}✓ SSH ключи найдены${NC}"
    if ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no -p "$SSH_PORT" "$SERVER_USER@$SERVER_IP" "echo 'KEY_AUTH_OK'" 2>&1 | grep -q "KEY_AUTH_OK"; then
        echo -e "${GREEN}✓ Аутентификация по ключу работает${NC}"
    else
        echo -e "${YELLOW}⚠ Аутентификация по ключу не настроена${NC}"
        echo "   Будет использоваться аутентификация по паролю"
    fi
else
    echo -e "${YELLOW}⚠ SSH ключи не найдены${NC}"
    echo "   Будет использоваться аутентификация по паролю"
    echo ""
    echo "Для создания SSH ключа выполните:"
    echo "  ssh-keygen -t ed25519 -C 'your_email@example.com'"
    echo ""
    echo "Для копирования ключа на сервер:"
    echo "  ssh-copy-id -p $SSH_PORT $SERVER_USER@$SERVER_IP"
fi

# Тестовое подключение
echo ""
echo "5. Тестовое подключение..."
echo "Попытка выполнить команду на сервере..."
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -p "$SSH_PORT" "$SERVER_USER@$SERVER_IP" "echo 'Тест подключения успешен'; hostname; whoami" 2>&1; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✓ SSH подключение работает корректно!"
    echo "==========================================${NC}"
    echo ""
    echo "Для подключения используйте:"
    echo "  ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠ Подключение требует ввода пароля или настройки ключей${NC}"
    echo ""
    echo "Попробуйте подключиться вручную:"
    echo "  ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP"
    echo ""
fi

