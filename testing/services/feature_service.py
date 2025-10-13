"""
Сервисный слой для управления функционалом тестирования.

Содержит бизнес-логику для создания, обновления и управления функционалом.
"""

import logging
from typing import Dict, List, Optional, Tuple

from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone

from shift_log.models import Employee
from shift_log.utils import log_activity, send_notification

from ..models import (Feature, FeatureComment, FeatureCommentHistory,
                      FeatureStatusHistory, TestProject)

logger = logging.getLogger(__name__)


class FeatureService:
    """Сервис для управления функционалом тестирования"""

    @staticmethod
    def create_feature(
        employee: Employee,
        test_project: TestProject,
        title: str,
        description: str,
        priority: int = 2
    ) -> Feature:
        """
        Создает новый функционал для тестирования
        
        Args:
            employee: Сотрудник, создающий функционал
            test_project: Тестовый проект
            title: Название функционала
            description: Описание функционала
            priority: Приоритет (1-4)
            
        Returns:
            Feature: Созданный функционал
            
        Raises:
            ValueError: Если сотрудник не может создавать функционал
        """
        if not FeatureService.can_create_feature(employee):
            raise ValueError("Сотрудник не может создавать функционал")
        
        with transaction.atomic():
            feature = Feature.objects.create(
                test_project=test_project,
                title=title,
                description=description,
                created_by=employee,
                priority=priority,
                status='new'
            )
            
            # Логируем создание
            log_activity(
                user=employee.user,
                action='created',
                model_name='Feature',
                object_id=feature.id,
                object_repr=str(feature),
                description=f"Создан функционал '{title}' в проекте '{test_project.name}'"
            )
            
            # Отправляем уведомления
            NotificationService.notify_feature_created(feature)
            
            logger.info(f"Создан функционал {feature.id} сотрудником {employee.user.username}")
            return feature

    @staticmethod
    def update_feature(
        feature: Feature,
        title: str,
        description: str,
        priority: int,
        employee: Employee
    ) -> Feature:
        """
        Обновляет данные функционала
        
        Args:
            feature: Функционал для обновления
            title: Новое название
            description: Новое описание
            priority: Новый приоритет
            employee: Сотрудник, обновляющий функционал
            
        Returns:
            Feature: Обновленный функционал
        """
        with transaction.atomic():
            old_title = feature.title
            old_description = feature.description
            old_priority = feature.priority
            
            feature.title = title
            feature.description = description
            feature.priority = priority
            feature.save()
            
            # Логируем изменения
            changes = []
            if old_title != title:
                changes.append(f"название: '{old_title}' → '{title}'")
            if old_description != description:
                changes.append(f"описание изменено")
            if old_priority != priority:
                changes.append(f"приоритет: {old_priority} → {priority}")
            
            if changes:
                log_activity(
                    employee.user,
                    'update',
                    'Feature',
                    feature.id,
                    str(feature),
                    description=f"Обновлен функционал: {', '.join(changes)}"
                )
            
            logger.info(f"Обновлен функционал {feature.id} сотрудником {employee.user.username}")
            return feature

    @staticmethod
    def update_feature_status(
        feature: Feature,
        new_status: str,
        employee: Employee,
        comment: str = ""
    ) -> Feature:
        """
        Обновляет статус функционала
        
        Args:
            feature: Функционал для обновления
            new_status: Новый статус
            employee: Сотрудник, изменяющий статус
            comment: Комментарий к изменению
            
        Returns:
            Feature: Обновленный функционал
            
        Raises:
            ValueError: Если переход статуса недопустим
        """
        if not FeatureService.can_change_status(feature, new_status, employee):
            raise ValueError("Недопустимый переход статуса")
        
        old_status = feature.status
        
        # Если статус не изменился, не делаем ничего
        if old_status == new_status:
            logger.info(f"Статус функционала {feature.id} не изменился ({old_status}), пропускаем обновление")
            return feature
        
        with transaction.atomic():
            # Обновляем статус
            feature.status = new_status
            if new_status == 'done':
                feature.completed_at = timezone.now()
            feature.save()
            
            # Создаем запись в истории
            FeatureStatusHistory.objects.create(
                feature=feature,
                old_status=old_status,
                new_status=new_status,
                changed_by=employee,
                comment=comment
            )
            
            # Логируем изменение
            log_activity(
                user=employee.user,
                action='status_changed',
                model_name='Feature',
                object_id=feature.id,
                object_repr=str(feature),
                description=f"Статус изменен с '{old_status}' на '{new_status}'",
                changes={
                    'old_status': old_status,
                    'new_status': new_status,
                    'comment': comment
                }
            )
            
            # Отправляем соответствующие уведомления
            NotificationService.notify_feature_status_changed(feature, old_status, new_status)
            
            logger.info(f"Статус функционала {feature.id} изменен с {old_status} на {new_status}")
            return feature

    @staticmethod
    def add_comment(
        feature: Feature,
        employee: Employee,
        comment_text: str,
        comment_type: str = 'remark'
    ) -> FeatureComment:
        """
        Добавляет замечание к функционалу
        
        Args:
            feature: Функционал
            employee: Автор замечания
            comment_text: Текст замечания
            comment_type: Тип замечания
            
        Returns:
            FeatureComment: Созданное замечание
        """
        with transaction.atomic():
            comment = FeatureComment.objects.create(
                feature=feature,
                author=employee,
                comment=comment_text,
                comment_type=comment_type
            )
            
            # Добавляем запись в историю замечания
            FeatureCommentHistory.objects.create(
                comment=comment,
                action='created',
                changed_by=employee,
                reason=f"Создано замечание типа '{comment.get_comment_type_display()}'"
            )
            
            # Логируем добавление замечания
            log_activity(
                user=employee.user,
                action='created',
                model_name='FeatureComment',
                object_id=comment.id,
                object_repr=str(comment),
                description=f"Добавлено замечание к функционалу '{feature.title}'"
            )
            
            # Отправляем уведомления
            NotificationService.notify_comment_added(feature, comment)
            
            logger.info(f"Добавлено замечание {comment.id} к функционалу {feature.id}")
            return comment

    @staticmethod
    def mark_as_completed(feature: Feature, employee: Employee) -> Feature:
        """
        Отмечает функционал как выполненный (для программистов)
        
        Args:
            feature: Функционал
            employee: Программист
            
        Returns:
            Feature: Обновленный функционал
        """
        if feature.status != 'rework':
            raise ValueError("Можно отмечать как выполненный только функционал на доработке")
        
        if employee.role != 'programmer' and employee.position != 'admin':
            raise ValueError("Только программисты могут отмечать функционал как выполненный")
        
        return FeatureService.update_feature_status(
            feature=feature,
            new_status='completed',
            employee=employee,
            comment="Функционал выполнен после доработки"
        )

    @staticmethod
    def resolve_comment_and_request_review(
        feature: Feature,
        comment: FeatureComment,
        employee: Employee
    ) -> Feature:
        """
        Отмечает замечание как решенное и запрашивает повторную проверку
        
        Args:
            feature: Функционал
            comment: Замечание для отметки как решенное
            employee: Программист
            
        Returns:
            Feature: Обновленный функционал
        """
        # Отмечаем замечание как решенное
        comment.mark_as_resolved(employee)
        
        # Добавляем запись в историю замечания
        FeatureCommentHistory.objects.create(
            comment=comment,
            action='resolved',
            changed_by=employee,
            reason="Замечание отмечено как решенное программистом"
        )
        
        # Логируем действие
        log_activity(
            employee.user,
            'comment_resolved',
            'FeatureComment',
            comment.id,
            str(comment),
            description=f"Замечание отмечено как решенное: {comment.comment[:50]}..."
        )
        
        # Обновляем объект feature из базы данных, чтобы получить актуальные данные
        feature.refresh_from_db()
        
        # Если все замечания решены, меняем статус на testing для повторной проверки
        unresolved_comments = feature.comments.filter(is_resolved=False)
        total_comments = feature.comments.count()
        resolved_comments = feature.comments.filter(is_resolved=True).count()
        
        logger.info(f"Функционал {feature.id}: всего замечаний = {total_comments}, решенных = {resolved_comments}, нерешенных = {unresolved_comments.count()}")
        
        if not unresolved_comments.exists():
            logger.info(f"Все замечания решены для функционала {feature.id}")
            # Отправляем уведомление о решении замечания
            NotificationService.notify_comment_resolved(feature, comment, employee)
            
            # Если функционал не в статусе testing, меняем статус
            if feature.status != 'testing':
                logger.info(f"Меняем статус с {feature.status} на testing")
                return FeatureService.update_feature_status(
                    feature=feature,
                    new_status='testing',
                    employee=employee,
                    comment=f"Все замечания исправлены. Требуется повторная проверка."
                )
            else:
                logger.info(f"Функционал уже в статусе testing, статус не меняем")
                return feature
        else:
            logger.info(f"Остались нерешенные замечания для функционала {feature.id}, статус остается {feature.status}")
            # Отправляем уведомление о решении замечания
            NotificationService.notify_comment_resolved(feature, comment, employee)
            return feature

    @staticmethod
    def return_comment_to_rework(
        feature: Feature,
        comment: FeatureComment,
        employee: Employee,
        reason: str = ""
    ) -> FeatureComment:
        """
        Возвращает замечание на доработку
        
        Args:
            feature: Функционал
            comment: Замечание для возврата на доработку
            employee: Тестировщик/администратор
            reason: Причина возврата на доработку
            
        Returns:
            FeatureComment: Обновленное замечание
        """
        if not (employee.role == 'tester' or employee.position == 'admin'):
            raise PermissionError("Только тестировщики и администраторы могут возвращать замечания на доработку")
        
        if not comment.is_resolved:
            raise ValueError("Можно возвращать на доработку только решенные замечания")
        
        with transaction.atomic():
            # Возвращаем замечание на доработку
            comment.is_resolved = False
            comment.rework_reason = reason
            comment.save()
            
            # Логируем действие
            log_activity(
                employee.user,
                'comment_returned_to_rework',
                'FeatureComment',
                comment.id,
                str(comment),
                description=f"Замечание возвращено на доработку: {comment.comment[:50]}... Причина: {reason}"
            )
            
            # Меняем статус функционала на доработку
            if feature.status == 'testing':
                FeatureService.update_feature_status(
                    feature=feature,
                    new_status='rework',
                    employee=employee,
                    comment=f"Замечание возвращено на доработку. Причина: {reason}"
                )
            
            # Отправляем уведомление
            NotificationService.notify_comment_returned_to_rework(feature, comment, employee, reason)
            
            logger.info(f"Замечание {comment.id} возвращено на доработку сотрудником {employee.user.username}")
            return comment

    @staticmethod
    def return_feature_to_rework(
        feature: Feature,
        employee: Employee,
        comment: str = ""
    ) -> Feature:
        """
        Возвращает функционал на доработку
        
        Args:
            feature: Функционал для возврата на доработку
            employee: Тестировщик/администратор
            comment: Комментарий к возврату
            
        Returns:
            Feature: Обновленный функционал
        """
        if not (employee.role == 'tester' or employee.position == 'admin'):
            raise PermissionError("Только тестировщики и администраторы могут возвращать функционал на доработку")
        
        if feature.status not in ['testing', 'completed']:
            raise ValueError("Можно возвращать на доработку только функционал со статусом 'testing' или 'completed'")
        
        return FeatureService.update_feature_status(
            feature=feature,
            new_status='rework',
            employee=employee,
            comment=comment or "Возвращено на доработку тестировщиком"
        )

    @staticmethod
    def can_create_feature(employee: Employee) -> bool:
        """Проверяет, может ли сотрудник создавать функционал"""
        return (
            employee.position == 'admin' or 
            employee.role == 'programmer'
        )

    @staticmethod
    def can_change_status(feature: Feature, new_status: str, employee: Employee) -> bool:
        """Проверяет, может ли сотрудник изменить статус"""
        current_status = feature.status
        
        # Администраторы могут все
        if employee.position == 'admin':
            return True
        
        # Тестировщики могут управлять статусами
        if employee.role == 'tester':
            return True
        
        # Программисты могут отмечать как выполненный и запрашивать повторную проверку
        if employee.role == 'programmer' and employee == feature.created_by:
            if current_status == 'rework' and new_status == 'completed':
                return True
            # Разрешаем переход на testing при отметке замечаний как решенных
            if new_status == 'testing':
                return True
        
        return False

    @staticmethod
    def get_available_status_transitions(feature: Feature, employee: Employee) -> List[str]:
        """Возвращает доступные переходы статусов для сотрудника"""
        current_status = feature.status
        transitions = []
        
        if employee.position == 'admin':
            # Администраторы могут все
            transitions = ['testing', 'rework', 'completed', 'done']
        elif employee.role == 'tester':
            # Тестировщики могут управлять процессом тестирования
            if current_status == 'new':
                transitions = ['testing']
            elif current_status == 'testing':
                transitions = ['rework', 'completed']
            elif current_status == 'completed':
                transitions = ['done', 'rework']
        elif employee.role == 'programmer' and employee == feature.created_by:
            # Программисты могут отмечать как выполненный и запрашивать повторную проверку
            if current_status == 'rework':
                transitions = ['completed']
            # Программисты могут запрашивать повторную проверку при решении замечаний
            transitions.append('testing')
        
        return transitions


class NotificationService:
    """Сервис для отправки уведомлений о тестировании"""

    @staticmethod
    def notify_feature_created(feature: Feature) -> None:
        """Отправляет уведомления о создании функционала"""
        # Получаем всех тестировщиков и администраторов
        recipients = Employee.objects.filter(
            models.Q(role='tester') | models.Q(position='admin'),
            is_active=True
        ).exclude(id=feature.created_by.id)
        
        for recipient in recipients:
            send_notification(
                recipient=recipient,
                notification_type='feature_created',
                title=f'Новый функционал: {feature.title}',
                message=f'Создан новый функционал "{feature.title}" в проекте "{feature.test_project.name}". '
                       f'Приоритет: {feature.get_priority_display()}. '
                       f'Описание: {feature.description[:200]}{"..." if len(feature.description) > 200 else ""}'
            )

    @staticmethod
    def notify_feature_status_changed(
        feature: Feature, 
        old_status: str, 
        new_status: str
    ) -> None:
        """Отправляет уведомления об изменении статуса"""
        notification_type_map = {
            'testing': 'feature_testing',
            'rework': 'feature_rework', 
            'completed': 'feature_completed',
            'done': 'feature_done'
        }
        
        notification_type = notification_type_map.get(new_status)
        if not notification_type:
            return
        
        # Определяем получателей в зависимости от статуса
        if new_status == 'testing':
            # Уведомляем тестировщиков и администраторов
            recipients = Employee.objects.filter(
                models.Q(role='tester') | models.Q(position='admin'),
                is_active=True
            )
        elif new_status == 'rework':
            # Уведомляем создателя и администраторов
            recipients = [feature.created_by]
            recipients.extend(Employee.objects.filter(position='admin', is_active=True))
        elif new_status == 'completed':
            # Уведомляем тестировщиков и администраторов
            recipients = Employee.objects.filter(
                models.Q(role='tester') | models.Q(position='admin'),
                is_active=True
            )
        elif new_status == 'done':
            # Уведомляем всех участников
            recipients = [feature.created_by]
            recipients.extend(Employee.objects.filter(
                models.Q(role='tester') | models.Q(position='admin'),
                is_active=True
            ))
        else:
            return
        
        # Убираем дубликаты
        recipients = list(set(recipients))
        
        status_names = dict(Feature.STATUS_CHOICES)
        old_status_name = status_names.get(old_status, old_status)
        new_status_name = status_names.get(new_status, new_status)
        
        for recipient in recipients:
            send_notification(
                recipient=recipient,
                notification_type=notification_type,
                title=f'Статус изменен: {feature.title}',
                message=f'Статус функционала "{feature.title}" изменен с "{old_status_name}" на "{new_status_name}". '
                       f'Проект: {feature.test_project.name}'
            )

    @staticmethod
    def notify_comment_added(feature: Feature, comment: FeatureComment) -> None:
        """Отправляет уведомления о добавлении замечания"""
        # Уведомляем создателя функционала (если это не он сам)
        if comment.author != feature.created_by:
            send_notification(
                recipient=feature.created_by,
                notification_type='feature_comment_added',
                title=f'Новое замечание: {feature.title}',
                message=f'Добавлено замечание к функционалу "{feature.title}" от {comment.author.get_full_name()}. '
                       f'Тип: {comment.get_comment_type_display()}. '
                       f'Текст: {comment.comment[:200]}{"..." if len(comment.comment) > 200 else ""}'
            )
        
        # Уведомляем администраторов
        admins = Employee.objects.filter(position='admin', is_active=True)
        for admin in admins:
            if admin != comment.author:
                send_notification(
                    recipient=admin,
                    notification_type='feature_comment_added',
                    title=f'Новое замечание: {feature.title}',
                    message=f'Добавлено замечание к функционалу "{feature.title}" от {comment.author.get_full_name()}. '
                           f'Тип: {comment.get_comment_type_display()}'
                )


    @staticmethod
    def notify_comment_returned_to_rework(
        feature: Feature, 
        comment: FeatureComment, 
        returned_by: Employee, 
        reason: str
    ) -> None:
        """Отправляет уведомления о возврате замечания на доработку"""
        # Уведомляем создателя функционала (если это не тот, кто вернул)
        if comment.feature.created_by != returned_by:
            send_notification(
                recipient=comment.feature.created_by,
                notification_type='feature_comment_added',
                title=f'Замечание возвращено на доработку: {feature.title}',
                message=f'Замечание к функционалу "{feature.title}" возвращено на доработку тестировщиком {returned_by.get_full_name()}. '
                       f'Причина: {reason[:200]}{"..." if len(reason) > 200 else ""}'
            )
        
        # Уведомляем администраторов
        admins = Employee.objects.filter(position='admin', is_active=True)
        for admin in admins:
            if admin != returned_by:
                send_notification(
                    recipient=admin,
                    notification_type='feature_comment_added',
                    title=f'Замечание возвращено на доработку: {feature.title}',
                    message=f'Замечание к функционалу "{feature.title}" возвращено на доработку тестировщиком {returned_by.get_full_name()}. '
                           f'Причина: {reason[:100]}{"..." if len(reason) > 100 else ""}'
                )

    @staticmethod
    def notify_comment_resolved(feature: Feature, comment: FeatureComment, resolved_by: Employee) -> None:
        """Отправляет уведомления о решении замечания"""
        # Уведомляем создателя функционала (программиста) - если это не тот же человек
        if feature.created_by != resolved_by:
            send_notification(
                recipient=feature.created_by,
                notification_type='feature_comment_resolved',
                title=f'Замечание решено: {feature.title}',
                message=f'Замечание к функционалу "{feature.title}" решено программистом {resolved_by.get_full_name()}. '
                       f'Текст замечания: {comment.comment[:200]}{"..." if len(comment.comment) > 200 else ""}'
            )
        
        # Уведомляем тестировщиков проекта
        testers = Employee.objects.filter(role='tester', is_active=True)
        for tester in testers:
            if tester != resolved_by:
                send_notification(
                    recipient=tester,
                    notification_type='feature_comment_resolved',
                    title=f'Замечание решено: {feature.title}',
                    message=f'Замечание к функционалу "{feature.title}" решено программистом {resolved_by.get_full_name()}. '
                           f'Требуется повторная проверка. '
                           f'Текст замечания: {comment.comment[:200]}{"..." if len(comment.comment) > 200 else ""}'
                )
        
        # Уведомляем администраторов
        admins = Employee.objects.filter(position='admin', is_active=True)
        for admin in admins:
            if admin != resolved_by:
                send_notification(
                    recipient=admin,
                    notification_type='feature_comment_resolved',
                    title=f'Замечание решено: {feature.title}',
                    message=f'Замечание к функционалу "{feature.title}" решено программистом {resolved_by.get_full_name()}. '
                           f'Текст замечания: {comment.comment[:200]}{"..." if len(comment.comment) > 200 else ""}'
                )


class TestProjectService:
    """Сервис для управления тестовыми проектами"""

    @staticmethod
    def create_project(
        employee: Employee,
        name: str,
        description: str = ""
    ) -> TestProject:
        """
        Создает новый тестовый проект
        
        Args:
            employee: Сотрудник, создающий проект
            name: Название проекта
            description: Описание проекта
            
        Returns:
            TestProject: Созданный проект
        """
        if not TestProjectService.can_create_project(employee):
            raise ValueError("Сотрудник не может создавать проекты")
        
        with transaction.atomic():
            project = TestProject.objects.create(
                name=name,
                description=description,
                created_by=employee
            )
            
            # Логируем создание
            log_activity(
                user=employee.user,
                action='created',
                model_name='TestProject',
                object_id=project.id,
                object_repr=str(project),
                description=f"Создан тестовый проект '{name}'"
            )
            
            logger.info(f"Создан тестовый проект {project.id} сотрудником {employee.user.username}")
            return project

    @staticmethod
    def can_create_project(employee: Employee) -> bool:
        """Проверяет, может ли сотрудник создавать проекты"""
        return (
            employee.position == 'admin' or 
            employee.role == 'programmer'
        )
