from django.core.management.base import BaseCommand
from django.db import transaction

from shift_log.models import Attachment


class Command(BaseCommand):
    help = 'Очищает "сиротские" записи вложений (когда файл удален, но запись в БД осталась)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет удалено без выполнения'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Подробный вывод'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write('Поиск "сиротских" вложений...')
        
        # Получаем все вложения
        attachments = Attachment.objects.all()
        orphaned_attachments = []
        
        for attachment in attachments:
            # Проверяем существование файла
            if not attachment.file or not attachment.file.storage.exists(attachment.file.name):
                orphaned_attachments.append(attachment)
                if verbose:
                    self.stdout.write(
                        f'  Найдено "сиротское" вложение: {attachment.filename} '
                        f'(ID: {attachment.id})'
                    )
        
        if not orphaned_attachments:
            self.stdout.write(
                self.style.SUCCESS('"Сиротских" вложений не найдено')
            )
            return
        
        self.stdout.write(
            f'Найдено {len(orphaned_attachments)} "сиротских" вложений'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    'Режим предварительного просмотра - вложения не будут удалены'
                )
            )
            return
        
        # Удаляем "сиротские" вложения
        with transaction.atomic():
            deleted_count = 0
            for attachment in orphaned_attachments:
                try:
                    attachment.delete()
                    deleted_count += 1
                    if verbose:
                        self.stdout.write(
                            f'  Удалено: {attachment.filename} (ID: {attachment.id})'
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  Ошибка при удалении {attachment.filename}: {e}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Удалено {deleted_count} "сиротских" вложений'
            )
        ) 