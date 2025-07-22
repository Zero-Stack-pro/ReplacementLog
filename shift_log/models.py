from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Department(models.Model):
    """Модель отдела"""
    name = models.CharField(max_length=100, verbose_name="Название отдела")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    """Модель сотрудника"""
    POSITION_CHOICES = [
        ('employee', 'Сотрудник'),
        ('supervisor', 'Руководитель'),
        ('admin', 'Администратор'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Отдел")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='employee', verbose_name="Должность")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    telegram_id = models.CharField(max_length=50, blank=True, verbose_name="Telegram ID")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department.name}"

    @property
    def is_supervisor(self):
        return self.position in ['supervisor', 'admin']

    @property
    def is_admin(self):
        return self.position == 'admin'
    
    def can_create_tasks_for_department(self, department):
        """
        Проверяет, может ли сотрудник создавать задачи для указанного отдела
        
        Args:
            department: Отдел для проверки
            
        Returns:
            bool: True если может создавать задачи
        """
        if self.is_admin:
            # Администратор может создавать задачи для любого отдела
            return True
        elif self.is_supervisor:
            # Руководитель может создавать задачи только для своего отдела
            return self.department == department
        else:
            # Обычный сотрудник может создавать задачи только для своего отдела
            return self.department == department
    
    def can_assign_tasks_to_employee(self, target_employee):
        """
        Проверяет, может ли сотрудник назначать задачи другому сотруднику
        
        Args:
            target_employee: Сотрудник, которому назначается задача
            
        Returns:
            bool: True если может назначать
        """
        if self.is_admin:
            # Администратор может назначать задачи любому сотруднику
            return True
        elif self.is_supervisor:
            # Руководитель может назначать задачи сотрудникам своего отдела
            return self.department == target_employee.department
        else:
            # Обычный сотрудник может назначать задачи только себе
            return self.id == target_employee.id
    
    def can_manage_shift(self, shift):
        """
        Проверяет, может ли сотрудник управлять сменой
        
        Args:
            shift: Смена для проверки
            
        Returns:
            bool: True если может управлять
        """
        if self.is_admin:
            # Администратор может управлять любыми сменами
            return True
        elif self.is_supervisor:
            # Руководитель может управлять сменами своего отдела
            return self.department == shift.department
        else:
            # Обычный сотрудник может управлять только своими сменами
            return shift.employees.filter(id=self.id).exists()
    
    def can_view_department_data(self, department):
        """
        Проверяет, может ли сотрудник просматривать данные отдела
        
        Args:
            department: Отдел для проверки
            
        Returns:
            bool: True если может просматривать
        """
        if self.is_admin:
            # Администратор может просматривать данные всех отделов
            return True
        else:
            # Остальные сотрудники могут просматривать только свой отдел
            return self.department == department
    
    def get_available_departments_for_tasks(self):
        """
        Возвращает список отделов, для которых сотрудник может создавать задачи
        
        Returns:
            QuerySet: Отделы доступные для создания задач
        """
        if self.is_admin:
            return Department.objects.all()
        elif self.is_supervisor:
            return Department.objects.filter(id=self.department.id)
        else:
            return Department.objects.none()
    
    def get_available_employees_for_assignments(self):
        """
        Возвращает список сотрудников, которым можно назначать задачи
        
        Returns:
            QuerySet: Сотрудники доступные для назначения задач
        """
        if self.is_admin:
            return Employee.objects.filter(is_active=True)
        elif self.is_supervisor:
            return Employee.objects.filter(
                department=self.department,
                is_active=True
            )
        else:
            return Employee.objects.none()
    
    def get_position_display_name(self):
        """Возвращает читаемое название должности"""
        position_names = {
            'employee': 'Сотрудник',
            'supervisor': 'Руководитель',
            'admin': 'Администратор',
        }
        return position_names.get(self.position, self.position)


class ShiftType(models.Model):
    """Модель типа смены - определяет периодичность и длительность"""
    SHIFT_PATTERN_CHOICES = [
        ('daily', 'Ежедневная'),
        ('weekly_5_2', 'Недельная (5/2)'),
        ('weekly_2_2', 'Недельная (2/2)'),
        ('weekly_3_1', 'Недельная (3/1)'),
        ('monthly', 'Месячная'),
        ('custom', 'Пользовательская'),
    ]
    
    PERIODICITY_CHOICES = [
        ('daily', 'Каждый день'),
        ('every_2_days', 'Через день'),
        ('every_3_days', 'Каждые 3 дня'),
        ('weekly', 'Раз в неделю'),
        ('biweekly', 'Раз в две недели'),
        ('monthly', 'Раз в месяц'),
        ('custom', 'Пользовательская'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Название типа смены")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Отдел")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    # Время смены
    start_time = models.TimeField(verbose_name="Время начала смены")
    end_time = models.TimeField(verbose_name="Время окончания смены")
    
    # Периодичность
    periodicity = models.CharField(
        max_length=20,
        choices=PERIODICITY_CHOICES,
        default='daily',
        verbose_name="Периодичность смены"
    )
    
    # Длительность
    duration_hours = models.IntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name="Длительность смены (часов)"
    )
    
    # Дополнительные параметры
    is_overnight = models.BooleanField(
        default=False,
        verbose_name="Ночная смена"
    )
    
    # Рабочие дни (для недельных паттернов)
    working_days = models.CharField(
        max_length=50,
        default='1,2,3,4,5',
        verbose_name="Рабочие дни недели (1-Пн, 2-Вт, 3-Ср, 4-Чт, 5-Пт, 6-Сб, 7-Вс)"
    )
    
    # День месяца (для месячных смен)
    day_of_month = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="День месяца (для месячных смен)"
    )
    
    # Пользовательские параметры
    custom_interval_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Интервал в днях (для пользовательской периодичности)"
    )
    
    # Цвет для отображения
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name="Цвет смены (HEX)"
    )
    
    # Активность
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    # Дата начала действия
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата начала действия (необязательно)"
    )
    
    # Дата окончания действия (опционально)
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата окончания действия (необязательно)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Тип смены"
        verbose_name_plural = "Типы смен"
        ordering = ['department', 'start_time']

    def __str__(self):
        periodicity_display = dict(self.PERIODICITY_CHOICES)[self.periodicity]
        return f"{self.name} ({self.start_time} - {self.end_time}, {periodicity_display})"
    
    def get_working_days_list(self):
        """Возвращает список рабочих дней как числа"""
        if not self.working_days:
            return []
        return [int(day.strip()) for day in self.working_days.split(',') if day.strip().isdigit()]
    
    def get_shift_duration(self):
        """Возвращает длительность смены в часах"""
        if self.is_overnight:
            # Для ночных смен считаем через полночь
            from datetime import datetime, timedelta
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            if end <= start:
                end += timedelta(days=1)
            return (end - start).total_seconds() / 3600
        else:
            return self.duration_hours
    
    def get_next_shift_date(self, from_date):
        """Возвращает дату следующей смены от указанной даты"""
        from datetime import timedelta
        
        if self.periodicity == 'daily':
            return from_date + timedelta(days=1)
        elif self.periodicity == 'every_2_days':
            return from_date + timedelta(days=2)
        elif self.periodicity == 'every_3_days':
            return from_date + timedelta(days=3)
        elif self.periodicity == 'weekly':
            return from_date + timedelta(days=7)
        elif self.periodicity == 'biweekly':
            return from_date + timedelta(days=14)
        elif self.periodicity == 'monthly':
            # Простая логика для месячных смен
            next_date = from_date + timedelta(days=28)
            if self.day_of_month:
                # Устанавливаем конкретный день месяца
                next_date = next_date.replace(day=min(self.day_of_month, 28))
            return next_date
        elif self.periodicity == 'custom' and self.custom_interval_days:
            return from_date + timedelta(days=self.custom_interval_days)
        else:
            return from_date + timedelta(days=1)
    
    def is_working_day(self, date):
        """Проверяет, является ли дата рабочим днем для этого типа смены"""
        if self.periodicity in ['daily', 'every_2_days', 'every_3_days', 'custom']:
            return True  # Эти периодичности работают каждый день
        
        weekday = date.isoweekday()  # 1=Понедельник, 7=Воскресенье
        return weekday in self.get_working_days_list()
    
    def get_periodicity_description(self):
        """Возвращает читаемое описание периодичности"""
        base_desc = dict(self.PERIODICITY_CHOICES)[self.periodicity]
        
        if self.periodicity == 'custom' and self.custom_interval_days:
            return f"Каждые {self.custom_interval_days} дней"
        elif self.periodicity == 'monthly' and self.day_of_month:
            return f"Каждый {self.day_of_month} день месяца"
        else:
            return base_desc


class Shift(models.Model):
    """Модель конкретной смены - экземпляр типа смены на определенную дату"""
    date = models.DateField(verbose_name="Дата смены")
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, verbose_name="Тип смены")
    employees = models.ManyToManyField(Employee, through='ShiftAssignment', verbose_name="Сотрудники")
    
    # Статус смены
    is_completed = models.BooleanField(default=False, verbose_name="Завершена")
    is_cancelled = models.BooleanField(default=False, verbose_name="Отменена")
    
    # Время фактического начала и окончания (может отличаться от планового)
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name="Фактическое время начала")
    actual_end_time = models.DateTimeField(null=True, blank=True, verbose_name="Фактическое время окончания")
    
    # Примечания к смене
    notes = models.TextField(blank=True, verbose_name="Примечания")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Смена"
        verbose_name_plural = "Смены"
        ordering = ['-date', 'shift_type__start_time']
        unique_together = ['date', 'shift_type']

    def __str__(self):
        return f"{self.date} - {self.shift_type.name} ({self.shift_type.get_periodicity_description()})"

    @property
    def department(self):
        return self.shift_type.department
    
    @property
    def planned_start_time(self):
        """Плановое время начала смены"""
        from datetime import datetime
        return datetime.combine(self.date, self.shift_type.start_time)
    
    @property
    def planned_end_time(self):
        """Плановое время окончания смены"""
        from datetime import datetime, timedelta
        end_time = self.shift_type.end_time
        end_datetime = datetime.combine(self.date, end_time)
        
        # Если смена переходит через полночь
        if self.shift_type.is_overnight and end_time < self.shift_type.start_time:
            end_datetime += timedelta(days=1)
        
        return end_datetime
    
    @property
    def duration_hours(self):
        """Длительность смены в часах"""
        return self.shift_type.get_shift_duration()
    
    @property
    def is_active(self):
        """Активна ли смена (не отменена и не завершена)"""
        return not self.is_cancelled and not self.is_completed
    
    @property
    def status_display(self):
        """Отображаемый статус смены"""
        if self.is_cancelled:
            return "Отменена"
        elif self.is_completed:
            return "Завершена"
        else:
            return "Активна"


class ShiftAssignment(models.Model):
    """Модель назначения сотрудника на смену"""
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, verbose_name="Смена")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    is_primary = models.BooleanField(default=False, verbose_name="Основной сотрудник")
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата назначения")

    class Meta:
        verbose_name = "Назначение на смену"
        verbose_name_plural = "Назначения на смены"
        unique_together = ['shift', 'employee']


class Task(models.Model):
    """Модель задания"""
    PRIORITY_CHOICES = [
        (1, 'Низкий'),
        (2, 'Средний'),
        (3, 'Высокий'),
        (4, 'Критический'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]

    TASK_TYPE_CHOICES = [
        ('maintenance', 'Обслуживание'),
        ('development', 'Разработка'),
        ('support', 'Поддержка'),
        ('emergency', 'Экстренная'),
        ('routine', 'Рутинная'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    comment = models.TextField(blank=True, verbose_name="Комментарий к заданию")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Отдел")
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Назначен на")
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='created_tasks', verbose_name="Создано")
    
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2, verbose_name="Приоритет")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='routine', verbose_name="Тип задачи")
    
    due_date = models.DateTimeField(verbose_name="Срок выполнения")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return self.title

    def get_status_color(self):
        """Возвращает цвет для статуса задания"""
        from .utils import get_task_status_color
        return get_task_status_color(self.status)

    def get_priority_color(self):
        """Возвращает цвет для приоритета задания"""
        from .utils import get_priority_color
        return get_priority_color(self.priority)
    
    def get_related_notifications(self):
        """Возвращает уведомления, связанные с этой задачей"""
        from .models import Notification
        return Notification.objects.filter(
            message__icontains=self.title
        ).order_by('-sent_at')
    
    @property
    def is_overdue(self):
        """Проверяет, просрочена ли задача"""
        from django.utils import timezone
        return (
            self.status not in ['completed', 'cancelled'] and 
            self.due_date < timezone.now()
        )

    @property
    def activity_logs(self):
        """Возвращает записи активности для этого задания"""
        from .models import ActivityLog
        return ActivityLog.objects.filter(
            model_name='Task',
            object_id=self.id
        ).order_by('-timestamp')

    @property
    def attachments(self):
        """Возвращает вложения для этого задания"""
        from .models import Attachment
        return Attachment.objects.filter(
            attachment_type='task',
            object_id=self.id
        ).order_by('-uploaded_at')


class ShiftLog(models.Model):
    """Модель журнала смены"""
    shift = models.OneToOneField(Shift, on_delete=models.CASCADE, verbose_name="Смена")
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Создан")
    
    start_notes = models.TextField(blank=True, verbose_name="Заметки начала смены")
    end_notes = models.TextField(blank=True, verbose_name="Заметки окончания смены")
    handover_notes = models.TextField(blank=True, verbose_name="Заметки передачи смены")
    
    is_completed = models.BooleanField(default=False, verbose_name="Завершен")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Журнал смены"
        verbose_name_plural = "Журналы смен"
        ordering = ['-created_at']

    def __str__(self):
        return f"Журнал смены {self.shift}"


class TaskReport(models.Model):
    """Модель отчета по заданию"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задание")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    
    report_text = models.TextField(verbose_name="Текст отчета")
    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, verbose_name="Статус")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Отчет по заданию"
        verbose_name_plural = "Отчеты по заданиям"
        ordering = ['-created_at']

    def __str__(self):
        return f"Отчет по заданию {self.task.title}"


class Attachment(models.Model):
    """Модель вложения (файлы, скриншоты)"""
    ATTACHMENT_TYPE_CHOICES = [
        ('task', 'Задание'),
        ('shift_log', 'Журнал смены'),
        ('task_report', 'Отчет по заданию'),
    ]

    file = models.FileField(upload_to='attachments/', verbose_name="Файл")
    filename = models.CharField(max_length=255, verbose_name="Имя файла")
    content_type = models.CharField(max_length=100, verbose_name="Тип контента")
    file_size = models.IntegerField(verbose_name="Размер файла")
    
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES, verbose_name="Тип вложения")
    object_id = models.IntegerField(verbose_name="ID объекта")
    
    uploaded_by = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Загружен")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Вложение"
        verbose_name_plural = "Вложения"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename


class Notification(models.Model):
    """Модель уведомления"""
    NOTIFICATION_TYPE_CHOICES = [
        ('task_assigned', 'Задание назначено'),
        ('shift_started', 'Смена началась'),
        ('shift_completed', 'Смена завершена'),
        ('task_completed', 'Задание завершено'),
        ('handover', 'Передача смены'),
    ]

    recipient = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Получатель")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, verbose_name="Тип уведомления")
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    message = models.TextField(verbose_name="Сообщение")
    
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата прочтения")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.title} - {self.recipient}"
    
    def get_type_color(self):
        """Возвращает цвет для типа уведомления"""
        colors = {
            'task_assigned': 'primary',
            'shift_started': 'success',
            'shift_completed': 'info',
            'task_completed': 'success',
            'handover': 'warning',
        }
        return colors.get(self.notification_type, 'secondary')
    
    def get_related_task(self):
        """Возвращает связанную задачу, если уведомление относится к задаче"""
        if self.notification_type in ['task_assigned', 'task_completed']:
            # Извлекаем название задачи из сообщения
            task_title = self.extract_task_title()
            if task_title:
                try:
                    return Task.objects.filter(title=task_title).first()
                except Task.DoesNotExist:
                    return None
        return None
    
    def extract_task_title(self):
        """Извлекает название задачи из сообщения уведомления"""
        import re

        # Паттерны для извлечения названия задачи
        patterns = [
            r'задание "([^"]+)"',  # задание "Название"
            r'задачу "([^"]+)"',   # задачу "Название"
            r'задания "([^"]+)"',  # задания "Название"
            r'задачи "([^"]+)"',   # задачи "Название"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Если не найдено в кавычках, ищем в заголовке
        if self.title.startswith('Новое задание: '):
            return self.title.replace('Новое задание: ', '')
        elif self.title.startswith('Статус задачи изменен: '):
            return self.title.replace('Статус задачи изменен: ', '')
        
        return None
    
    def is_task_related(self):
        """Проверяет, относится ли уведомление к задаче"""
        return self.notification_type in ['task_assigned', 'task_completed']
    
    def get_task_url(self):
        """Возвращает URL для перехода к задаче, если уведомление связано с задачей"""
        task = self.get_related_task()
        if task:
            return reverse('shift_log:task_detail', kwargs={'pk': task.pk})
        return None


class ActivityLog(models.Model):
    """Модель журнала активности (история изменений)"""
    ACTION_CHOICES = [
        ('created', 'Создано'),
        ('updated', 'Обновлено'),
        ('deleted', 'Удалено'),
        ('status_changed', 'Статус изменен'),
        ('assigned', 'Назначено'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    action = models.CharField(max_length=100, choices=ACTION_CHOICES, verbose_name="Действие")
    model_name = models.CharField(max_length=100, verbose_name="Модель")
    object_id = models.IntegerField(verbose_name="ID объекта")
    object_repr = models.CharField(max_length=200, verbose_name="Представление объекта")
    description = models.TextField(blank=True, verbose_name="Описание")
    changes = models.JSONField(null=True, blank=True, verbose_name="Изменения")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    class Meta:
        verbose_name = "Запись активности"
        verbose_name_plural = "Записи активности"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.object_repr} ({self.timestamp})"
    
    @property
    def created_at(self):
        """Алиас для timestamp для совместимости с шаблоном"""
        return self.timestamp


class DailyReport(models.Model):
    department = models.ForeignKey(
        'Department', on_delete=models.CASCADE, related_name='daily_reports'
    )
    date = models.DateField()
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('department', 'date')
        ordering = ['-date']
        verbose_name = 'Ежедневный отчёт'
        verbose_name_plural = 'Ежедневные отчёты'

    def __str__(self):
        return f"{self.department} — {self.date}"

UNIT_CHOICES = [
    ('m', 'м'),
    ('pcs', 'шт'),
] 
class MaterialWriteOff(models.Model):
    """Списание материалов"""
    material_name = models.CharField(
        max_length=255,
        verbose_name="Что списали"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сколько списали"
    )
    
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs')
    
    destination = models.CharField(
        max_length=255,
        verbose_name="Куда"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name="Отдел"
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name="Кем списано"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время списания"
    )

    class Meta:
        verbose_name = "Списание материала"
        verbose_name_plural = "Списания материалов"
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.material_name} ({self.quantity}) для {self.destination} "
            f"— {self.department.name}"
        )


class Project(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='projects', verbose_name='Сотрудник')
    name = models.CharField(max_length=100, verbose_name='Название проекта')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        unique_together = ('employee', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class Note(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notes', verbose_name='Сотрудник')
    title = models.CharField(max_length=200, verbose_name='Название', blank=True, default='')
    text = models.TextField(verbose_name='Текст заметки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Заметка'
        verbose_name_plural = 'Заметки'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Заметка {self.employee.user.get_full_name()} ({self.created_at:%d.%m.%Y})"


class ProjectTask(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('done', 'Завершена'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name='Проект')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='project_tasks', verbose_name='Сотрудник')
    title = models.CharField(max_length=200, verbose_name='Название задачи')
    description = models.TextField(blank=True, verbose_name='Описание')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Время исполнения')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Задача проекта'
        verbose_name_plural = 'Задачи проектов'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
