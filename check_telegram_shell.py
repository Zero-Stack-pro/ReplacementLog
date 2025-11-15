#!/usr/bin/env python
"""
Скрипт для проверки настроек Telegram через Django shell
Использование: python check_telegram_shell.py
Или через Django shell: python manage.py shell < check_telegram_shell.py
"""
import os
import sys
import django

# Настройка Django
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shift_log_project.settings')
    django.setup()

from django.conf import settings
from shift_log.models import Employee, Notification
from shift_log.services.telegram_service import TelegramService
import asyncio

print('=== Проверка настроек Telegram ===\n')

# Проверка токена
token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
if token:
    masked_token = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
    print(f'✓ TELEGRAM_BOT_TOKEN установлен: {masked_token}')
else:
    print('✗ TELEGRAM_BOT_TOKEN не установлен!')
    print('  Установите переменную окружения: export TELEGRAM_BOT_TOKEN="ваш_токен"')

# Проверка флага включения
enabled = getattr(settings, 'TELEGRAM_NOTIFICATIONS_ENABLED', True)
if enabled:
    print(f'✓ TELEGRAM_NOTIFICATIONS_ENABLED: {enabled}')
else:
    print(f'⚠ TELEGRAM_NOTIFICATIONS_ENABLED: {enabled} (уведомления отключены)')

# Проверка бота
print('\n--- Проверка подключения к боту ---')
bot = TelegramService.get_bot()
if bot:
    try:
        async def get_bot_info():
            return await bot.get_me()
        
        try:
            bot_info = asyncio.run(get_bot_info())
            print(f'✓ Бот подключен: @{bot_info.username} ({bot_info.first_name})')
        except Exception as e:
            print(f'✗ Ошибка при получении информации о боте: {e}')
    except Exception as e:
        print(f'✗ Ошибка при создании бота: {e}')
else:
    print('✗ Не удалось создать экземпляр бота')

# Проверка сотрудников с telegram_id
print('\n--- Сотрудники с настроенным Telegram ID ---')
employees_with_telegram = Employee.objects.filter(
    telegram_id__isnull=False
).exclude(telegram_id='')

if employees_with_telegram.exists():
    print(f'✓ Найдено сотрудников: {employees_with_telegram.count()}')
    for emp in employees_with_telegram:
        status = '✓' if emp.is_active else '⚠'
        print(f'  {status} {emp.get_full_name()} ({emp.user.username}): {emp.telegram_id}')
else:
    print('⚠ Нет сотрудников с настроенным telegram_id')

# Проверка последних уведомлений
print('\n--- Последние уведомления ---')
recent_notifications = Notification.objects.order_by('-sent_at')[:5]
if recent_notifications.exists():
    for notif in recent_notifications:
        telegram_status = '✓' if notif.recipient.telegram_id else '✗'
        print(f'  {telegram_status} {notif.title} → {notif.recipient.get_full_name()} ({notif.sent_at})')
else:
    print('⚠ Нет уведомлений в базе данных')

print('\n=== Проверка завершена ===')







