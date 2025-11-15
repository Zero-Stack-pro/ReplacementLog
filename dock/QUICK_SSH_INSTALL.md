# Быстрая установка SSH на сервере

## Текущий статус

✅ Сервер доступен (ping успешен)  
❌ SSH порт 22 недоступен - требуется установка SSH сервера

## Что нужно сделать

### Вариант 1: Если есть доступ к серверу через консоль провайдера/другой способ

1. **Подключитесь к серверу** любым доступным способом (консоль провайдера, физический доступ, и т.д.)

2. **Выполните установку SSH:**

   **Для Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y openssh-server
   sudo systemctl start ssh
   sudo systemctl enable ssh
   sudo ufw allow ssh
   ```

   **Для CentOS/RHEL:**
   ```bash
   sudo yum install -y openssh-server
   sudo systemctl start sshd
   sudo systemctl enable sshd
   sudo firewall-cmd --permanent --add-service=ssh
   sudo firewall-cmd --reload
   ```

3. **Проверьте статус:**
   ```bash
   sudo systemctl status ssh
   # или
   sudo systemctl status sshd
   ```

### Вариант 2: Использование скрипта установки

Если можете скопировать файл на сервер:

1. **Скопируйте скрипт на сервер** (через другой способ доступа):
   ```bash
   # Например, через scp с другого сервера, или вручную через консоль
   ```

2. **На сервере выполните:**
   ```bash
   chmod +x install_ssh_server.sh
   sudo ./install_ssh_server.sh
   ```

## После установки

Вернитесь на локальную машину и выполните проверку:

```bash
./scripts/check_ssh_connection.sh
```

Или попробуйте подключиться вручную:

```bash
ssh zero@10.45.20.40
```

## Если SSH уже установлен, но порт закрыт

Проверьте файрвол:

```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow ssh

# CentOS/RHEL
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

Проверьте, что SSH запущен:

```bash
sudo systemctl start ssh
sudo systemctl enable ssh
```

## Быстрая проверка на сервере

Выполните на сервере:

```bash
# Проверка установки
which sshd
sshd -V

# Проверка статуса
sudo systemctl status ssh

# Проверка порта
sudo netstat -tlnp | grep :22
# или
sudo ss -tlnp | grep :22
```

