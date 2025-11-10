import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (ActivityLog, Department, Employee, Notification, Shift,
                     ShiftType)
from .services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


def log_activity(user, action, model_name, object_id, object_repr, description="", changes=None):
    """
    Логирует активность пользователя
    
    Args:
        user: Пользователь, выполнивший действие
        action: Тип действия (create, update, delete, etc.)
        model_name: Название модели
        object_id: ID объекта
        object_repr: Строковое представление объекта
        description: Описание действия (опционально)
        changes: Словарь с изменениями (опционально)
    """
    try:
        ActivityLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            description=description,
            changes=changes
        )
    except Exception as e:
        logger.error(f"Error logging activity: {e}")


def send_notification(
    recipient: Employee,
    notification_type: str,
    title: str,
    message: str
) -> None:
    """
    Отправляет уведомление пользователю
    
    Args:
        recipient: Получатель уведомления (Employee)
        notification_type: Тип уведомления
        title: Заголовок уведомления
        message: Текст уведомления
    """
    try:
        Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message
        )
        
        # Отправляем уведомление в Telegram, если у сотрудника указан telegram_id
        if recipient.telegram_id and settings.TELEGRAM_NOTIFICATIONS_ENABLED:
            send_telegram_notification(recipient, title, message)
        
        # Здесь можно добавить отправку через email
        # send_email_notification(recipient, title, message)
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")


def send_telegram_notification(employee: Employee, title: str, message: str) -> None:
    """
    Отправляет уведомление через Telegram
    
    Args:
        employee: Сотрудник
        title: Заголовок уведомления
        message: Текст уведомления
    """
    if not employee.telegram_id:
        logger.debug(f"У сотрудника {employee} не указан telegram_id, пропускаем отправку")
        return
    
    try:
        logger.info(f"Попытка отправки Telegram уведомления: {title} → {employee.get_full_name()} (telegram_id: {employee.telegram_id})")
        result = TelegramService.send_message(
            chat_id=employee.telegram_id,
            title=title,
            message=message
        )
        if result:
            logger.info(f"✓ Telegram уведомление успешно отправлено: {title} → {employee.get_full_name()}")
        else:
            logger.warning(f"✗ Telegram уведомление не отправлено (вернуло False): {title} → {employee.get_full_name()}")
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение основного потока
        logger.error(f"Error sending Telegram notification to {employee}: {e}", exc_info=True)


def send_email_notification(employee, title, message):
    """
    Отправляет уведомление по email
    
    Args:
        employee: Сотрудник
        title: Заголовок уведомления
        message: Текст уведомления
    """
    try:
        # Здесь должна быть интеграция с email сервисом
        # Например, через Django Email Backend
        pass
    except Exception as e:
        logger.error(f"Error sending email notification: {e}")


def get_employee_permissions(employee):
    """
    Возвращает права доступа сотрудника
    
    Args:
        employee: Сотрудник
        
    Returns:
        dict: Словарь с правами доступа
    """
    permissions = {
        'can_view_all_departments': False,
        'can_manage_departments': False,
        'can_create_tasks': False,
        'can_edit_tasks': False,
        'can_delete_tasks': False,
        'can_manage_employees': False,
        'can_view_reports': False,
    }
    
    if not employee:
        return permissions
    
    if employee.position == 'admin':
        permissions.update({
            'can_view_all_departments': True,
            'can_manage_departments': True,
            'can_create_tasks': True,
            'can_edit_tasks': True,
            'can_delete_tasks': True,
            'can_manage_employees': True,
            'can_view_reports': True,
        })
    elif employee.position == 'supervisor':
        permissions.update({
            'can_view_all_departments': False,
            'can_manage_departments': False,
            'can_create_tasks': True,
            'can_edit_tasks': True,
            'can_delete_tasks': False,
            'can_manage_employees': False,
            'can_view_reports': True,
        })
    else:  # employee
        permissions.update({
            'can_view_all_departments': False,
            'can_manage_departments': False,
            'can_create_tasks': False,
            'can_edit_tasks': False,
            'can_delete_tasks': False,
            'can_manage_employees': False,
            'can_view_reports': False,
        })
    
    return permissions


def format_file_size(size_bytes):
    """
    Форматирует размер файла в читаемый вид
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        str: Отформатированный размер
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_task_status_color(status: str) -> str:
    """Возвращает цвет для статуса задания"""
    colors = {
        'pending': 'warning',
        'in_progress': 'primary',
        'rework': 'danger',
        'completed': 'success',
        'cancelled': 'danger',
    }
    return colors.get(status, 'secondary')


def get_priority_color(priority: int) -> str:
    """Возвращает цвет для приоритета задания"""
    colors = {
        1: 'success',  # Низкий
        2: 'info',     # Средний
        3: 'warning',  # Высокий
        4: 'danger',   # Критический
    }
    return colors.get(priority, 'secondary')


def create_shifts_for_period(
    shift_type: ShiftType,
    start_date: date,
    end_date: date,
    employees: Optional[List[Employee]] = None
) -> List[Shift]:
    """
    Создает смены для указанного периода на основе паттерна типа смены
    
    Args:
        shift_type: Тип смены
        start_date: Начальная дата
        end_date: Конечная дата
        employees: Список сотрудников для назначения (опционально)
    
    Returns:
        Список созданных смен
    """
    created_shifts = []
    current_date = start_date
    
    with transaction.atomic():
        while current_date <= end_date:
            if shift_type.is_working_day(current_date):
                # Проверяем, не существует ли уже смена на эту дату
                shift, created = Shift.objects.get_or_create(
                    date=current_date,
                    shift_type=shift_type,
                    defaults={
                        'is_completed': False,
                    }
                )
                
                if created:
                    # Назначаем сотрудников, если они указаны
                    if employees:
                        shift.employees.set(employees)
                    
                    created_shifts.append(shift)
                    logger.info(f"Создана смена: {shift}")
            
            current_date += timedelta(days=1)
    
    return created_shifts


def generate_shift_schedule(
    department: Department,
    start_date: date,
    end_date: date,
    employees: Optional[List[Employee]] = None
) -> dict:
    """
    Генерирует расписание смен для отдела на указанный период
    
    Args:
        department: Отдел
        start_date: Начальная дата
        end_date: Конечная дата
        employees: Список сотрудников (опционально)
    
    Returns:
        Словарь с результатами генерации
    """
    shift_types = ShiftType.objects.filter(
        department=department,
        is_active=True
    )
    
    results = {
        'department': department.name,
        'period': f"{start_date} - {end_date}",
        'total_shifts_created': 0,
        'shifts_by_type': {},
        'errors': []
    }
    
    for shift_type in shift_types:
        try:
            shifts = create_shifts_for_period(
                shift_type=shift_type,
                start_date=start_date,
                end_date=end_date,
                employees=employees
            )
            
            results['shifts_by_type'][shift_type.name] = len(shifts)
            results['total_shifts_created'] += len(shifts)
            
        except Exception as e:
            error_msg = f"Ошибка при создании смен типа '{shift_type.name}': {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
    
    return results


def get_employee_schedule(
    employee: Employee,
    start_date: date,
    end_date: date
) -> List[Shift]:
    """
    Получает расписание смен для конкретного сотрудника
    
    Args:
        employee: Сотрудник
        start_date: Начальная дата
        end_date: Конечная дата
    
    Returns:
        Список смен сотрудника
    """
    return Shift.objects.filter(
        employees=employee,
        date__range=[start_date, end_date]
    ).order_by('date', 'shift_type__start_time')


def get_department_schedule(
    department: Department,
    start_date: date,
    end_date: date
) -> List[Shift]:
    """
    Получает расписание смен для отдела
    
    Args:
        department: Отдел
        start_date: Начальная дата
        end_date: Конечная дата
    
    Returns:
        Список смен отдела
    """
    return Shift.objects.filter(
        shift_type__department=department,
        date__range=[start_date, end_date]
    ).order_by('date', 'shift_type__start_time')


def calculate_shift_duration(shift_type: ShiftType) -> float:
    """
    Вычисляет длительность смены в часах
    
    Args:
        shift_type: Тип смены
    
    Returns:
        Длительность в часах
    """
    if shift_type.is_overnight:
        # Для ночных смен считаем через полночь
        start = datetime.combine(datetime.today(), shift_type.start_time)
        end = datetime.combine(datetime.today(), shift_type.end_time)
        if end <= start:
            end += timedelta(days=1)
        return (end - start).total_seconds() / 3600
    else:
        return shift_type.shift_duration_hours


def get_next_working_day(shift_type: ShiftType, from_date: date) -> Optional[date]:
    """
    Получает следующий рабочий день для типа смены
    
    Args:
        shift_type: Тип смены
        from_date: Дата, от которой искать
    
    Returns:
        Следующий рабочий день или None
    """
    return shift_type.get_next_shift_date(from_date)


def validate_shift_pattern(shift_type: ShiftType) -> List[str]:
    """
    Валидирует паттерн смены
    
    Args:
        shift_type: Тип смены
    
    Returns:
        Список ошибок валидации
    """
    errors = []
    
    # Проверяем рабочие дни
    working_days = shift_type.get_working_days_list()
    if not working_days:
        errors.append("Не указаны рабочие дни")
    
    # Проверяем выходные дни
    rest_days = shift_type.get_rest_days_list()
    if not rest_days:
        errors.append("Не указаны выходные дни")
    
    # Проверяем пересечение рабочих и выходных дней
    intersection = set(working_days) & set(rest_days)
    if intersection:
        errors.append(f"Дни {intersection} указаны и как рабочие, и как выходные")
    
    # Проверяем время смены
    if shift_type.start_time >= shift_type.end_time and not shift_type.is_overnight:
        errors.append("Время окончания должно быть больше времени начала для дневных смен")
    
    # Проверяем длительность
    if shift_type.shift_duration_hours < 1 or shift_type.shift_duration_hours > 24:
        errors.append("Длительность смены должна быть от 1 до 24 часов")
    
    return errors


def get_shift_pattern_description(shift_type: ShiftType) -> str:
    """
    Возвращает описание паттерна смены
    
    Args:
        shift_type: Тип смены
    
    Returns:
        Описание паттерна
    """
    pattern_names = {
        'daily': 'Ежедневная',
        'weekly': 'Недельная (5/2)',
        'weekly_alt': 'Недельная (2/2)',
        'monthly': 'Месячная',
        'custom': 'Пользовательская',
    }
    
    pattern_name = pattern_names.get(shift_type.shift_pattern, 'Неизвестный')
    
    if shift_type.shift_pattern == 'custom':
        working_days = shift_type.get_working_days_list()
        rest_days = shift_type.get_rest_days_list()
        
        day_names = {
            1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 
            5: 'Пт', 6: 'Сб', 7: 'Вс'
        }
        
        working_names = [day_names.get(day, str(day)) for day in working_days]
        rest_names = [day_names.get(day, str(day)) for day in rest_days]
        
        return f"Пользовательская: {', '.join(working_names)} / {', '.join(rest_names)}"
    
    return pattern_name 