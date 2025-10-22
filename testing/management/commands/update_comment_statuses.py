"""
Команда для обновления статусов существующих замечаний.

Обновляет статусы замечаний в соответствии с новыми полями модели.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from testing.models import FeatureComment


class Command(BaseCommand):
    """Команда для обновления статусов замечаний"""
    
    help = 'Обновляет статусы существующих замечаний в соответствии с новыми полями модели'

    def handle(self, *args, **options):
        """Выполняет обновление статусов замечаний"""
        self.stdout.write('Начинаем обновление статусов замечаний...')
        
        with transaction.atomic():
            # Обновляем замечания, которые были отмечены как решенные
            resolved_comments = FeatureComment.objects.filter(is_resolved=True)
            resolved_count = resolved_comments.count()
            
            if resolved_count > 0:
                resolved_comments.update(status='resolved')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Обновлено {resolved_count} решенных замечаний'
                    )
                )
            
            # Остальные замечания остаются в статусе 'open'
            open_comments = FeatureComment.objects.filter(is_resolved=False)
            open_count = open_comments.count()
            
            if open_count > 0:
                open_comments.update(status='open')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Обновлено {open_count} открытых замечаний'
                    )
                )
        
        total_comments = FeatureComment.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Обновление завершено. Всего замечаний: {total_comments}'
            )
        )
