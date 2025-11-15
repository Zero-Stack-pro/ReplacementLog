"""Management команда для проверки настроек Telegram"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

from shift_log.models import Employee
from shift_log.services.telegram_service import TelegramService


class Command(BaseCommand):
    """Команда для проверки настроек Telegram"""
    
    help = 'Проверяет настройки Telegram уведомлений'

    def handle(self, *args, **options):
        """Обрабатывает команду"""
        self.stdout.write(self.style.SUCCESS('=== Проверка настроек Telegram ===\n'))
        
        # Проверка токена
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if token:
            masked_token = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
            self.stdout.write(self.style.SUCCESS(f'✓ TELEGRAM_BOT_TOKEN установлен: {masked_token}'))
        else:
            self.stdout.write(self.style.ERROR('✗ TELEGRAM_BOT_TOKEN не установлен!'))
            self.stdout.write(self.style.WARNING('  Установите переменную окружения: export TELEGRAM_BOT_TOKEN="ваш_токен"'))
        
        # Проверка флага включения
        enabled = getattr(settings, 'TELEGRAM_NOTIFICATIONS_ENABLED', True)
        if enabled:
            self.stdout.write(self.style.SUCCESS(f'✓ TELEGRAM_NOTIFICATIONS_ENABLED: {enabled}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ TELEGRAM_NOTIFICATIONS_ENABLED: {enabled} (уведомления отключены)'))
        
        # Проверка бота
        self.stdout.write('\n--- Проверка подключения к боту ---')
        bot = TelegramService.get_bot()
        if bot:
            try:
                # Пробуем получить информацию о боте
                import asyncio
                async def get_bot_info():
                    return await bot.get_me()
                
                try:
                    bot_info = asyncio.run(get_bot_info())
                    self.stdout.write(self.style.SUCCESS(f'✓ Бот подключен: @{bot_info.username} ({bot_info.first_name})'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Ошибка при получении информации о боте: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Ошибка при создании бота: {e}'))
        else:
            self.stdout.write(self.style.ERROR('✗ Не удалось создать экземпляр бота'))
        
        # Проверка сотрудников с telegram_id
        self.stdout.write('\n--- Сотрудники с настроенным Telegram ID ---')
        employees_with_telegram = Employee.objects.filter(
            telegram_id__isnull=False
        ).exclude(telegram_id='')
        
        if employees_with_telegram.exists():
            self.stdout.write(self.style.SUCCESS(f'✓ Найдено сотрудников: {employees_with_telegram.count()}'))
            for emp in employees_with_telegram:
                status = '✓' if emp.is_active else '⚠'
                self.stdout.write(f'  {status} {emp.get_full_name()} ({emp.user.username}): {emp.telegram_id}')
        else:
            self.stdout.write(self.style.WARNING('⚠ Нет сотрудников с настроенным telegram_id'))
        
        # Проверка последних уведомлений
        self.stdout.write('\n--- Последние уведомления ---')
        from shift_log.models import Notification
        recent_notifications = Notification.objects.order_by('-sent_at')[:5]
        if recent_notifications.exists():
            for notif in recent_notifications:
                telegram_status = '✓' if notif.recipient.telegram_id else '✗'
                self.stdout.write(f'  {telegram_status} {notif.title} → {notif.recipient.get_full_name()} ({notif.sent_at})')
        else:
            self.stdout.write(self.style.WARNING('⚠ Нет уведомлений в базе данных'))
        
        self.stdout.write('\n' + self.style.SUCCESS('=== Проверка завершена ==='))







