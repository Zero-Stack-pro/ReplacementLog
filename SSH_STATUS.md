# Статус SSH подключения к серверу

## ✅ SSH успешно настроен и работает!

**Дата проверки:** 2025-11-10  
**Сервер:** ReplacementLog-VM (10.45.20.40)  
**Пользователь:** zero

## Информация о сервере

- **IP адрес:** 10.45.20.40
- **Имя хоста:** ReplacementLog-VM
- **ОС:** Ubuntu 24.04 (Linux 6.14.0-27-generic)
- **SSH версия:** OpenSSH_9.6p1 Ubuntu-3ubuntu13.14
- **Порт SSH:** 22
- **Uptime:** 96 дней

## Статус SSH

✅ **SSH сервер установлен и работает**  
✅ **Порт 22 открыт и доступен**  
✅ **SSH ключи настроены** - подключение без пароля работает  
✅ **Проверка подключения успешна**

## Способы подключения

### 1. Простое подключение (по ключу, без пароля)

```bash
ssh zero@10.45.20.40
```

### 2. Через скрипт подключения

```bash
# Интерактивное подключение
./scripts/connect_to_server.sh

# Выполнение команды на сервере
./scripts/connect_to_server.sh "команда"
```

### 3. С указанием порта

```bash
ssh -p 22 zero@10.45.20.40
```

## Выполнение команд на сервере

### Через SSH напрямую:

```bash
ssh zero@10.45.20.40 "команда"
```

### Через скрипт:

```bash
./scripts/connect_to_server.sh "команда"
```

### Примеры:

```bash
# Проверка статуса
./scripts/connect_to_server.sh "hostname; uptime"

# Проверка Django
./scripts/connect_to_server.sh "cd /path/to/project && python manage.py check"

# Проверка логов
./scripts/connect_to_server.sh "tail -f /var/log/app.log"
```

## Копирование файлов

### SCP (Secure Copy):

```bash
# Копирование файла на сервер
scp file.txt zero@10.45.20.40:/path/to/destination/

# Копирование с сервера
scp zero@10.45.20.40:/path/to/file.txt ./

# Копирование директории
scp -r directory/ zero@10.45.20.40:/path/to/destination/
```

### RSYNC (синхронизация):

```bash
# Синхронизация проекта
rsync -avz --exclude 'venv' --exclude '__pycache__' \
  ./ zero@10.45.20.40:/path/to/project/
```

## Настройка SSH ключей

SSH ключи уже настроены и работают. Если нужно настроить на другой машине:

```bash
# 1. Создать ключ (если еще нет)
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. Скопировать ключ на сервер
ssh-copy-id zero@10.45.20.40

# 3. Проверить подключение
ssh zero@10.45.20.40
```

## Проверка SSH

Используйте скрипт проверки:

```bash
./scripts/check_ssh_connection.sh 10.45.20.40 zero 22
```

## Полезные команды для работы с сервером

### Информация о системе:

```bash
./scripts/connect_to_server.sh "hostname; uname -a; uptime; df -h"
```

### Проверка Django проекта:

```bash
./scripts/connect_to_server.sh "cd /path/to/project && python manage.py check"
```

### Проверка процессов:

```bash
./scripts/connect_to_server.sh "ps aux | grep python"
```

### Проверка логов:

```bash
./scripts/connect_to_server.sh "tail -n 50 /var/log/app.log"
```

## Безопасность

⚠️ **Рекомендации:**

1. ✅ SSH ключи настроены - хорошо
2. ⚠️ Рассмотрите возможность отключения аутентификации по паролю после полной настройки ключей
3. ⚠️ Рассмотрите изменение стандартного порта SSH (опционально)
4. ⚠️ Настройте fail2ban для защиты от брутфорса

## Следующие шаги

Теперь вы можете:

1. ✅ Подключаться к серверу через SSH
2. ✅ Выполнять команды на сервере
3. ✅ Копировать файлы на/с сервера
4. ✅ Настраивать Django приложение
5. ✅ Проверять логи и статус сервисов
6. ✅ Настраивать переменные окружения
7. ✅ Запускать management команды Django

## Документация

- `SSH_SETUP.md` - Полная документация по установке SSH
- `scripts/check_ssh_connection.sh` - Скрипт проверки SSH
- `scripts/connect_to_server.sh` - Скрипт подключения к серверу
- `scripts/install_ssh_server.sh` - Скрипт установки SSH (если понадобится)

