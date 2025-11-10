#!/bin/bash
# Скрипт для подключения к серверу
# Использует SSH ключи (если настроены) или пароль
# Использование: ./connect_to_server.sh [команда]

set -e

SERVER_IP="10.45.20.40"
SERVER_USER="zero"
SERVER_PASSWORD="33423342"
SSH_PORT="22"

# Параметры SSH
SSH_OPTS="-o StrictHostKeyChecking=no -p $SSH_PORT"

# Проверка подключения по ключу
if ssh $SSH_OPTS -o BatchMode=yes -o ConnectTimeout=3 "$SERVER_USER@$SERVER_IP" "echo 'key_ok'" &>/dev/null; then
    # Подключение по ключу (без пароля)
    if [ -n "$1" ]; then
        ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$@"
    else
        ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP"
    fi
else
    # Подключение с паролем через sshpass
    if ! command -v sshpass &> /dev/null; then
        echo "Установка sshpass для подключения с паролем..."
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
    
    if [ -n "$1" ]; then
        sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$@"
    else
        sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP"
    fi
fi

