from django.core.management.base import BaseCommand

from shift_log.models import Attachment, Task


class Command(BaseCommand):
    help = 'Проверяет вложения в базе данных'

    def handle(self, *args, **options):
        self.stdout.write('Проверка вложений...')
        
        # Проверяем все вложения
        attachments = Attachment.objects.all()
        self.stdout.write(f'Всего вложений: {attachments.count()}')
        
        for attachment in attachments:
            self.stdout.write(
                f'  ID: {attachment.id}, '
                f'Файл: {attachment.filename}, '
                f'Тип: {attachment.attachment_type}, '
                f'Объект: {attachment.object_id}'
            )
        
        # Проверяем вложения для задач
        tasks = Task.objects.all()
        self.stdout.write(f'\nВсего задач: {tasks.count()}')
        
        for task in tasks:
            task_attachments = Attachment.objects.filter(
                attachment_type='task',
                object_id=task.id
            )
            if task_attachments.exists():
                self.stdout.write(
                    f'  Задача {task.id} ({task.title}): '
                    f'{task_attachments.count()} вложений'
                )
                for attachment in task_attachments:
                    self.stdout.write(
                        f'    - {attachment.filename} (ID: {attachment.id})'
                    ) 