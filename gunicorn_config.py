"""
Gunicorn configuration used by the systemd service.

Settings rely on environment variables so we can tune the process
without rebuilding the image or touching VCS-managed files.
"""
from __future__ import annotations

import multiprocessing
import os

CPU_COUNT: int = multiprocessing.cpu_count()

workers: int = int(os.environ.get("GUNICORN_WORKERS", CPU_COUNT * 2 + 1))
threads: int = int(os.environ.get("GUNICORN_THREADS", 2))

bind: str = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

timeout: int = int(os.environ.get("GUNICORN_TIMEOUT", 120))
keepalive: int = int(os.environ.get("GUNICORN_KEEPALIVE", 5))

max_requests: int = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter: int = int(
    os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 100),
)

accesslog: str = os.environ.get(
    "GUNICORN_ACCESS_LOG",
    "/var/log/replacementlog-access.log",
)
errorlog: str = os.environ.get(
    "GUNICORN_ERROR_LOG",
    "/var/log/replacementlog-error.log",
)
loglevel: str = os.environ.get("GUNICORN_LOG_LEVEL", "info")
proc_name: str = "replacementlog"

reload: bool = False
preload_app: bool = True
graceful_timeout: int = int(
    os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 30),
)
worker_class: str = os.environ.get("GUNICORN_WORKER_CLASS", "sync")
worker_connections: int = int(
    os.environ.get("GUNICORN_WORKER_CONNECTIONS", 1000),
)
umask: int = int(os.environ.get("GUNICORN_UMASK", 0o007))

