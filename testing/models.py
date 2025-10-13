"""
Модели для приложения тестирования функционала.

Следует принципам DDD (Domain-Driven Design) и Django Best Practices.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from shift_log.models import Employee


class TestProject(models.Model):
    """Модель тестового проекта"""
    
    name = models.CharField(
        max_length=200, 
        verbose_name="Название проекта",
        help_text="Название тестового проекта"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Подробное описание проекта"
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='created_test_projects',
        verbose_name="Создатель",
        help_text="Сотрудник, создавший проект"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Активен ли проект"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Тестовый проект"
        verbose_name_plural = "Тестовые проекты"
        ordering = ['-created_at']
        unique_together = ['name', 'created_by']

    def __str__(self) -> str:
        return f"{self.name} ({self.created_by.get_full_name()})"

    def get_absolute_url(self) -> str:
        """Возвращает URL для детального просмотра проекта"""
        return reverse(
            'testing:testproject_detail', kwargs={'pk': self.pk}
        )

    @property
    def features_count(self) -> int:
        """Возвращает количество функционала в проекте"""
        return self.features.count()

    @property
    def active_features_count(self) -> int:
        """Возвращает количество активного функционала"""
        return self.features.exclude(status='done').count()


class Feature(models.Model):
    """Модель функционала для тестирования"""
    
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('testing', 'На тестировании'),
        ('rework', 'На доработке'),
        ('completed', 'Выполнено'),
        ('done', 'Завершено'),
    ]

    PRIORITY_CHOICES = [
        (1, 'Низкий'),
        (2, 'Средний'),
        (3, 'Высокий'),
        (4, 'Критический'),
    ]

    test_project = models.ForeignKey(
        TestProject,
        on_delete=models.CASCADE,
        related_name='features',
        verbose_name="Тестовый проект",
        help_text="Проект, к которому относится функционал"
    )
    title = models.CharField(
        max_length=300,
        verbose_name="Название функционала",
        help_text="Краткое описание функционала"
    )
    description = models.TextField(
        verbose_name="Описание",
        help_text="Подробное описание функционала"
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='created_features',
        verbose_name="Создатель",
        help_text="Сотрудник, создавший функционал"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус",
        help_text="Текущий статус функционала"
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        verbose_name="Приоритет",
        help_text="Приоритет функционала"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата завершения",
        help_text="Дата окончательного завершения"
    )

    class Meta:
        verbose_name = "Функционал"
        verbose_name_plural = "Функционал"
        ordering = ['-priority', '-created_at']

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"

    def get_absolute_url(self) -> str:
        """Возвращает URL для детального просмотра функционала"""
        return reverse(
            'testing:feature_detail', kwargs={'pk': self.pk}
        )

    @property
    def is_new(self) -> bool:
        """Проверяет, является ли функционал новым"""
        return self.status == 'new'

    @property
    def is_testing(self) -> bool:
        """Проверяет, находится ли функционал на тестировании"""
        return self.status == 'testing'

    @property
    def is_rework(self) -> bool:
        """Проверяет, находится ли функционал на доработке"""
        return self.status == 'rework'

    @property
    def is_completed(self) -> bool:
        """Проверяет, выполнен ли функционал"""
        return self.status == 'completed'

    @property
    def is_done(self) -> bool:
        """Проверяет, завершен ли функционал окончательно"""
        return self.status == 'done'

    @property
    def comments_count(self) -> int:
        """Возвращает количество замечаний"""
        return self.comments.count()

    @property
    def unresolved_comments_count(self) -> int:
        """Возвращает количество нерешенных замечаний"""
        return self.comments.filter(is_resolved=False).count()

    def can_be_edited_by(self, employee: Employee) -> bool:
        """Проверяет, может ли сотрудник редактировать функционал"""
        if employee.position == 'admin':
            return True
        elif employee.position == 'supervisor':
            return True
        elif (employee.role == 'programmer' and 
              self.created_by == employee):
            return self.status in ['new', 'rework']
        return False

    def can_change_status_by(self, employee: Employee) -> bool:
        """Проверяет, может ли сотрудник изменять статус"""
        if employee.position == 'admin':
            return True
        elif employee.role == 'tester':
            return True
        elif (employee.role == 'programmer' and 
              self.created_by == employee):
            return self.status == 'rework'
        return False


class FeatureComment(models.Model):
    """Модель замечания к функционалу"""
    
    COMMENT_TYPE_CHOICES = [
        ('remark', 'Замечание'),
        ('approval', 'Одобрение'),
        ('clarification', 'Уточнение'),
    ]

    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Функционал",
        help_text="Функционал, к которому относится замечание"
    )
    author = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='feature_comments',
        verbose_name="Автор",
        help_text="Сотрудник, оставивший замечание"
    )
    comment = models.TextField(
        verbose_name="Текст замечания",
        help_text="Содержание замечания"
    )
    comment_type = models.CharField(
        max_length=20,
        choices=COMMENT_TYPE_CHOICES,
        default='remark',
        verbose_name="Тип замечания",
        help_text="Тип комментария"
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name="Решено",
        help_text="Решено ли замечание"
    )
    rework_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Причина возврата на доработку",
        help_text="Причина возврата замечания на доработку"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Замечание к функционалу"
        verbose_name_plural = "Замечания к функционалу"
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Замечание к {self.feature.title} от {self.author.get_full_name()}"

    @property
    def is_remark(self) -> bool:
        """Проверяет, является ли замечание критическим"""
        return self.comment_type == 'remark'

    @property
    def is_approval(self) -> bool:
        """Проверяет, является ли замечание одобрением"""
        return self.comment_type == 'approval'

    def can_be_resolved_by(self, employee: Employee) -> bool:
        """Проверяет, может ли сотрудник отметить замечание как решенное"""
        if employee.position == 'admin':
            return True
        elif employee.role == 'programmer' and self.feature.created_by == employee:
            return True
        return False

    def mark_as_resolved(self, employee: Employee) -> None:
        """Отмечает замечание как решенное"""
        if not self.can_be_resolved_by(employee):
            raise PermissionError("У сотрудника нет прав для отметки замечания как решенного")
        
        self.is_resolved = True
        self.rework_reason = None  # Очищаем причину возврата на доработку
        self.save()
        
        # Проверяем, что замечание действительно сохранилось
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT is_resolved FROM testing_featurecomment WHERE id = %s", [self.id])
        result = cursor.fetchone()
        print(f"DEBUG: Проверка в БД - is_resolved = {result[0] if result else 'None'}")

    def can_be_returned_to_rework_by(self, employee: Employee) -> bool:
        """Проверяет, может ли сотрудник вернуть замечание на доработку"""
        if employee.position == 'admin':
            return True
        elif employee.role == 'tester':
            return True
        return False

    def return_to_rework(self, employee: Employee, reason: str) -> None:
        """Возвращает замечание на доработку"""
        if not self.can_be_returned_to_rework_by(employee):
            raise PermissionError("У сотрудника нет прав для возврата замечания на доработку")
        
        if not reason.strip():
            raise ValueError("Причина возврата на доработку обязательна")
        
        self.is_resolved = False
        self.rework_reason = reason.strip()
        self.save()


class FeatureCommentHistory(models.Model):
    """Модель истории изменений замечаний к функционалу"""
    
    ACTION_CHOICES = [
        ('created', 'Создано'),
        ('resolved', 'Решено'),
        ('returned_to_rework', 'Возвращено на доработку'),
        ('updated', 'Обновлено'),
    ]
    
    comment = models.ForeignKey(
        FeatureComment,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name="Замечание",
        help_text="Замечание, к которому относится история"
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name="Действие",
        help_text="Тип действия с замечанием"
    )
    changed_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='comment_changes',
        verbose_name="Изменил",
        help_text="Сотрудник, выполнивший действие"
    )
    reason = models.TextField(
        blank=True,
        verbose_name="Причина/Комментарий",
        help_text="Причина изменения или дополнительный комментарий"
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата изменения"
    )

    class Meta:
        verbose_name = "История замечания"
        verbose_name_plural = "История замечаний"
        ordering = ['-changed_at']

    def __str__(self) -> str:
        return f"{self.comment.feature.title} - {self.get_action_display()}"


class FeatureAttachment(models.Model):
    """Модель вложения к функционалу"""
    
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="Функционал",
        help_text="Функционал, к которому относится вложение"
    )
    file = models.FileField(
        upload_to='testing/attachments/',
        verbose_name="Файл",
        help_text="Загруженный файл"
    )
    filename = models.CharField(
        max_length=255,
        verbose_name="Имя файла",
        help_text="Оригинальное имя файла"
    )
    content_type = models.CharField(
        max_length=100,
        verbose_name="Тип контента",
        help_text="MIME-тип файла"
    )
    file_size = models.IntegerField(
        verbose_name="Размер файла",
        help_text="Размер файла в байтах"
    )
    uploaded_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='feature_attachments',
        verbose_name="Загружен",
        help_text="Сотрудник, загрузивший файл"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата загрузки"
    )

    class Meta:
        verbose_name = "Вложение к функционалу"
        verbose_name_plural = "Вложения к функционалу"
        ordering = ['-uploaded_at']

    def __str__(self) -> str:
        return f"{self.filename} ({self.feature.title})"

    def get_file_icon(self) -> str:
        """Возвращает иконку для типа файла"""
        content_type = self.content_type.lower()
        
        # Изображения
        if content_type.startswith('image/'):
            return 'bi-image'
        
        # PDF
        elif content_type == 'application/pdf':
            return 'bi-file-pdf'
        
        # Документы Word
        elif content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'bi-file-word'
        
        # Текстовые файлы
        elif content_type.startswith('text/'):
            return 'bi-file-text'
        
        # Архивы
        elif content_type in ['application/zip', 'application/x-rar-compressed']:
            return 'bi-file-zip'
        
        # JSON и XML
        elif content_type in ['application/json', 'application/xml']:
            return 'bi-file-code'
        
        # По умолчанию
        else:
            return 'bi-file-earmark'

    def is_viewable_in_browser(self) -> bool:
        """Проверяет, можно ли отобразить файл в браузере"""
        viewable_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
            'application/pdf',
            'text/plain', 'text/html', 'text/css', 'text/javascript',
            'application/json', 'application/xml'
        ]
        return self.content_type.lower() in viewable_types


class FeatureStatusHistory(models.Model):
    """Модель истории изменений статуса функционала"""
    
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name="Функционал"
    )
    old_status = models.CharField(
        max_length=20,
        choices=Feature.STATUS_CHOICES,
        verbose_name="Предыдущий статус"
    )
    new_status = models.CharField(
        max_length=20,
        choices=Feature.STATUS_CHOICES,
        verbose_name="Новый статус"
    )
    changed_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='feature_status_changes',
        verbose_name="Изменил"
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий",
        help_text="Комментарий к изменению статуса"
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата изменения"
    )

    class Meta:
        verbose_name = "История статуса функционала"
        verbose_name_plural = "История статусов функционала"
        ordering = ['-changed_at']

    def __str__(self) -> str:
        return f"{self.feature.title}: {self.old_status} → {self.new_status}"