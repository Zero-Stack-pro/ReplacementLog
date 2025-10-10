"""
Админ-панель для приложения тестирования функционала.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (Feature, FeatureAttachment, FeatureComment,
                     FeatureCommentHistory, FeatureStatusHistory, TestProject)


@admin.register(TestProject)
class TestProjectAdmin(admin.ModelAdmin):
    """Админ для тестовых проектов"""
    
    list_display = [
        'name', 'created_by', 'is_active', 'features_count', 'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'created_by__department']
    search_fields = ['name', 'description', 'created_by__user__first_name', 'created_by__user__last_name']
    raw_id_fields = ['created_by']
    readonly_fields = ['created_at', 'updated_at', 'features_count']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'created_by', 'is_active')
        }),
        ('Статистика', {
            'fields': ('features_count',),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def features_count(self, obj):
        """Возвращает количество функционала в проекте"""
        return obj.features.count()
    features_count.short_description = 'Количество функционала'


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    """Админ для функционала"""
    
    list_display = [
        'title', 'test_project', 'created_by', 'status', 'priority', 
        'comments_count', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'test_project', 'created_by__department', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'created_by__user__first_name', 
        'created_by__user__last_name', 'test_project__name'
    ]
    raw_id_fields = ['test_project', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'comments_count']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('test_project', 'title', 'description', 'created_by')
        }),
        ('Статус и приоритет', {
            'fields': ('status', 'priority')
        }),
        ('Статистика', {
            'fields': ('comments_count',),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def comments_count(self, obj):
        """Возвращает количество замечаний"""
        return obj.comments.count()
    comments_count.short_description = 'Количество замечаний'

    def get_queryset(self, request):
        """Оптимизирует запросы"""
        return super().get_queryset(request).select_related(
            'test_project', 'created_by', 'created_by__user'
        )


@admin.register(FeatureComment)
class FeatureCommentAdmin(admin.ModelAdmin):
    """Админ для замечаний к функционалу"""
    
    list_display = [
        'feature', 'author', 'comment_type', 'is_resolved', 'created_at'
    ]
    list_filter = [
        'comment_type', 'is_resolved', 'created_at', 'author__department'
    ]
    search_fields = [
        'comment', 'feature__title', 'author__user__first_name', 
        'author__user__last_name'
    ]
    raw_id_fields = ['feature', 'author']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('feature', 'author', 'comment_type', 'comment')
        }),
        ('Статус', {
            'fields': ('is_resolved',)
        }),
        ('Временные метки', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Оптимизирует запросы"""
        return super().get_queryset(request).select_related(
            'feature', 'author', 'author__user'
        )


@admin.register(FeatureAttachment)
class FeatureAttachmentAdmin(admin.ModelAdmin):
    """Админ для вложений к функционалу"""
    
    list_display = [
        'filename', 'feature', 'uploaded_by', 'file_size', 'uploaded_at'
    ]
    list_filter = ['uploaded_at', 'feature__test_project']
    search_fields = [
        'filename', 'feature__title', 'uploaded_by__user__first_name',
        'uploaded_by__user__last_name'
    ]
    raw_id_fields = ['feature', 'uploaded_by']
    readonly_fields = ['file_size', 'uploaded_at', 'content_type']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('feature', 'file', 'filename', 'uploaded_by')
        }),
        ('Метаданные файла', {
            'fields': ('content_type', 'file_size', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Оптимизирует запросы"""
        return super().get_queryset(request).select_related(
            'feature', 'uploaded_by', 'uploaded_by__user'
        )


@admin.register(FeatureStatusHistory)
class FeatureStatusHistoryAdmin(admin.ModelAdmin):
    """Админ для истории изменений статуса функционала"""
    
    list_display = [
        'feature', 'old_status', 'new_status', 'changed_by', 'changed_at'
    ]
    list_filter = [
        'old_status', 'new_status', 'changed_at', 'changed_by__department'
    ]
    search_fields = [
        'feature__title', 'changed_by__user__first_name',
        'changed_by__user__last_name', 'comment'
    ]
    raw_id_fields = ['feature', 'changed_by']
    readonly_fields = ['changed_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('feature', 'old_status', 'new_status', 'changed_by')
        }),
        ('Дополнительно', {
            'fields': ('comment', 'changed_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Оптимизирует запросы"""
        return super().get_queryset(request).select_related(
            'feature', 'changed_by', 'changed_by__user'
        )

    def has_add_permission(self, request):
        """Запрещает добавление записей истории вручную"""
        return False

    def has_change_permission(self, request, obj=None):
        """Запрещает редактирование истории"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещает удаление истории"""
        return False


@admin.register(FeatureCommentHistory)
class FeatureCommentHistoryAdmin(admin.ModelAdmin):
    """Админ для истории изменений замечаний"""
    
    list_display = [
        'comment', 'action', 'changed_by', 'changed_at'
    ]
    list_filter = [
        'action', 'changed_at', 'changed_by__department'
    ]
    search_fields = [
        'comment__feature__title', 'comment__comment', 'changed_by__user__first_name',
        'changed_by__user__last_name', 'reason'
    ]
    raw_id_fields = ['comment', 'changed_by']
    readonly_fields = ['changed_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('comment', 'action', 'changed_by')
        }),
        ('Дополнительно', {
            'fields': ('reason', 'changed_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Оптимизирует запросы"""
        return super().get_queryset(request).select_related(
            'comment', 'comment__feature', 'changed_by', 'changed_by__user'
        )

    def has_add_permission(self, request):
        """Запрещает добавление записей истории вручную"""
        return False

    def has_change_permission(self, request, obj=None):
        """Запрещает редактирование истории"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещает удаление истории"""
        return False