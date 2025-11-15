"""
Конфигурация Gunicorn для production
"""
import multiprocessing
import os

# Количество воркеров (рекомендуется: (2 x CPU cores) + 1)
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Количество потоков на воркер
threads = int(os.environ.get('GUNICORN_THREADS', 2))

# Биндинг
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# Таймауты
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 5))

# Лимиты запросов (для предотвращения утечек памяти)
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', 100))

# Логирование
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '/var/log/replacementlog-access.log')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '/var/log/replacementlog-error.log')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Имя приложения
proc_name = 'replacementlog'

# Пользователь и группа (будут установлены systemd)
# user = 'zero'
# group = 'zero'

# Перезагрузка при изменении кода (только для разработки)
reload = False

# Preload приложения для экономии памяти
preload_app = True

# Graceful timeout для перезапуска воркеров
graceful_timeout = int(os.environ.get('GUNICORN_GRACEFUL_TIMEOUT', 30))

# Worker class
worker_class = 'sync'  # sync для большинства случаев, gevent для async

# Worker connections (для gevent)
worker_connections = 1000

# PID файл (systemd управляет PID, но можно указать для совместимости)
# pidfile = '/var/run/replacementlog.pid'  # Закомментировано, так как systemd управляет процессом

# Daemon mode (будет управляться systemd)
daemon = False

# Umask
umask = 0o007

