"""Management команда для установки telegram_id сотруднику"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from shift_log.models import Employee


class Command(BaseCommand):
    """Команда для установки telegram_id сотруднику"""
    
    help = 'Устанавливает telegram_id для сотрудника по username'

    def add_arguments(self, parser):
        """Добавляет аргументы команды"""
        parser.add_argument(
            'username',
            type=str,
            help='Username сотрудника'
        )
        parser.add_argument(
            'telegram_id',
            type=str,
            help='Telegram ID сотрудника'
        )

    def handle(self, *args, **options):
        """Обрабатывает команду"""
        username = options['username']
        telegram_id = options['telegram_id']
        
        try:
            user = User.objects.get(username=username)
            employee = Employee.objects.get(user=user)
            
            employee.telegram_id = telegram_id
            employee.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно установлен telegram_id {telegram_id} для сотрудника {employee.get_full_name()} ({username})'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь с username "{username}" не найден')
            )
        except Employee.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Сотрудник для пользователя "{username}" не найден')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при обновлении: {e}')
            )

