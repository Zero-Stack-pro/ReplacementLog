import os

from django.conf import settings
from django.core.management.base import BaseCommand

from shift_log.models import DailyReportPhoto


class Command(BaseCommand):
    help = 'Очищает записи о несуществующих фотографиях из базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет удалено без фактического удаления',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('Поиск несуществующих фотографий...')

        photos = DailyReportPhoto.objects.all()
        deleted_count = 0

        for photo in photos:
            file_path = os.path.join(settings.MEDIA_ROOT, photo.image.name)
            if not os.path.exists(file_path):
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Будет удалено: {photo.image.name}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Удаляем: {photo.image.name}')
                    )
                    photo.delete()
                deleted_count += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Файл существует: {photo.image.name}')
                )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'Найдено {deleted_count} несуществующих записей'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Удалено {deleted_count} записей')
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Осталось фотографий в базе: '
                    f'{DailyReportPhoto.objects.count()}'
                )
            )
