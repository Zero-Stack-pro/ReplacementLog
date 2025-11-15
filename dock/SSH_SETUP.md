# Установка и настройка SSH на сервере

## Обзор

Это руководство поможет установить и настроить SSH сервер на удаленном сервере, а также проверить подключение с локальной машины.

## Предварительные требования

- Доступ к серверу (через консоль провайдера, физический доступ, или другой способ)
- Права root или sudo на сервере
- Локальная машина с установленным SSH клиентом

## Шаг 1: Установка SSH сервера на сервере

### Вариант A: Автоматическая установка (рекомендуется)

1. Скопируйте скрипт на сервер (если есть другой способ доступа):
   ```bash
   # С локальной машины, если есть другой способ передачи файлов
   scp scripts/install_ssh_server.sh user@server:/tmp/
   ```

2. На сервере выполните:
   ```bash
   chmod +x /tmp/install_ssh_server.sh
   sudo /tmp/install_ssh_server.sh
   ```

### Вариант B: Ручная установка

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y openssh-server
sudo systemctl start ssh
sudo systemctl enable ssh
```

#### CentOS/RHEL/Fedora:
```bash
sudo yum install -y openssh-server
sudo systemctl start sshd
sudo systemctl enable sshd
```

#### Проверка статуса:
```bash
sudo systemctl status ssh
# или
sudo systemctl status sshd
```

## Шаг 2: Настройка файрвола

### UFW (Ubuntu):
```bash
sudo ufw allow ssh
sudo ufw allow 22/tcp
sudo ufw status
```

### Firewalld (CentOS/RHEL):
```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### iptables (если используется):
```bash
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables-save
```

## Шаг 3: Проверка SSH подключения с локальной машины

### Автоматическая проверка

Выполните скрипт проверки на локальной машине:

```bash
chmod +x scripts/check_ssh_connection.sh
./scripts/check_ssh_connection.sh [IP_СЕРВЕРА] [ПОЛЬЗОВАТЕЛЬ] [ПОРТ]
```

Примеры:
```bash
# С параметрами по умолчанию (10.45.20.40, zero, 22)
./scripts/check_ssh_connection.sh

# С указанием IP
./scripts/check_ssh_connection.sh 10.45.20.40

# С указанием IP и пользователя
./scripts/check_ssh_connection.sh 10.45.20.40 zero

# С указанием всех параметров
./scripts/check_ssh_connection.sh 10.45.20.40 zero 22
```

### Ручная проверка

1. **Проверка доступности сервера:**
   ```bash
   ping 10.45.20.40
   ```

2. **Проверка порта SSH:**
   ```bash
   nc -zv 10.45.20.40 22
   # или
   telnet 10.45.20.40 22
   ```

3. **Проверка SSH версии:**
   ```bash
   ssh -v zero@10.45.20.40
   ```

4. **Тестовое подключение:**
   ```bash
   ssh zero@10.45.20.40 "echo 'SSH работает!'; hostname; whoami"
   ```

## Шаг 4: Настройка SSH ключей (рекомендуется)

### Создание SSH ключа на локальной машине

```bash
# Создание ключа (если еще нет)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Или RSA (для старых систем)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

### Копирование ключа на сервер

```bash
ssh-copy-id -p 22 zero@10.45.20.40
```

Или вручную:
```bash
cat ~/.ssh/id_ed25519.pub | ssh zero@10.45.20.40 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Проверка подключения по ключу

```bash
ssh zero@10.45.20.40
# Должно подключиться без запроса пароля
```

## Шаг 5: Усиление безопасности SSH (опционально)

После настройки ключей рекомендуется:

1. **Отключить аутентификацию по паролю:**
   ```bash
   sudo nano /etc/ssh/sshd_config
   ```
   
   Измените:
   ```
   PasswordAuthentication no
   ```

2. **Отключить вход root:**
   ```
   PermitRootLogin no
   ```

3. **Изменить стандартный порт (опционально):**
   ```
   Port 2222
   ```
   
   Не забудьте открыть новый порт в файрволе!

4. **Перезапустить SSH:**
   ```bash
   sudo systemctl restart ssh
   # или
   sudo systemctl restart sshd
   ```

## Устранение проблем

### SSH сервер не запускается

```bash
# Проверка логов
sudo journalctl -u ssh -n 50
# или
sudo journalctl -u sshd -n 50

# Проверка конфигурации
sudo sshd -t
```

### Не могу подключиться

1. **Проверьте файрвол:**
   ```bash
   sudo ufw status
   # или
   sudo firewall-cmd --list-all
   ```

2. **Проверьте, что SSH слушает на правильном интерфейсе:**
   ```bash
   sudo netstat -tlnp | grep ssh
   # или
   sudo ss -tlnp | grep ssh
   ```

3. **Проверьте логи SSH:**
   ```bash
   sudo tail -f /var/log/auth.log  # Ubuntu/Debian
   sudo tail -f /var/log/secure    # CentOS/RHEL
   ```

### Проблемы с ключами

```bash
# Проверка прав на ключи
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Проверка владельца
sudo chown -R $USER:$USER ~/.ssh
```

## Быстрая справка

### Информация о сервере

```bash
# IP адрес сервера
hostname -I

# Имя хоста
hostname

# Версия SSH
sshd -V
```

### Полезные команды SSH

```bash
# Подключение
ssh user@server

# Подключение с указанием порта
ssh -p 2222 user@server

# Выполнение команды на удаленном сервере
ssh user@server "command"

# Копирование файлов (SCP)
scp file.txt user@server:/path/to/destination/

# Копирование директории
scp -r directory/ user@server:/path/to/destination/

# Копирование с указанием порта
scp -P 2222 file.txt user@server:/path/
```

## Конфигурация для проекта

Для данного проекта сервер находится по адресу:
- **IP:** 10.45.20.40
- **Пользователь:** zero (предположительно)
- **Порт:** 22 (стандартный)

После установки SSH вы сможете:
- Подключаться к серверу для настройки приложения
- Копировать файлы проекта
- Выполнять команды Django на сервере
- Настраивать переменные окружения
- Проверять логи и статус сервисов

