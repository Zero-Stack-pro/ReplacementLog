from django.contrib import admin
from django.utils.html import format_html

from .models import (ActivityLog, Attachment, DailyReport, DailyReportPhoto,
                     Department, Employee, MaterialWriteOff, Note,
                     Notification, Project, ProjectTask, Task, TaskReport)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'department', 'position', 'phone', 'is_active', 'created_at'
    ]
    list_filter = ['department', 'position', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    raw_id_fields = ['user']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'department', 'assigned_to', 'priority', 'status',
        'task_type', 'due_date', 'created_at'
    ]
    list_filter = [
        'department', 'priority', 'status', 'task_type', 'created_at'
    ]
    search_fields = ['title', 'description', 'comment']
    raw_id_fields = ['assigned_to', 'created_by']
    date_hierarchy = 'created_at'
    list_editable = ['status', 'priority']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'comment', 'department', 'assigned_to', 'created_by')
        }),
        ('Детали задания', {
            'fields': ('priority', 'status', 'task_type', 'due_date', 'completed_at')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TaskReport)
class TaskReportAdmin(admin.ModelAdmin):
    list_display = [
        'task', 'employee', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['task__title', 'report_text']
    raw_id_fields = ['task', 'employee']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'attachment_type', 'uploaded_by', 'file_size', 'uploaded_at'
    ]
    list_filter = ['attachment_type', 'uploaded_at']
    search_fields = ['filename']
    raw_id_fields = ['uploaded_by']
    readonly_fields = ['file_size', 'uploaded_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'recipient', 'notification_type', 'title', 'is_read', 'sent_at'
    ]
    list_filter = ['notification_type', 'is_read', 'sent_at']
    search_fields = ['title', 'message', 'recipient__user__username']
    raw_id_fields = ['recipient']
    readonly_fields = ['sent_at', 'read_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'action', 'model_name', 'object_repr', 'timestamp'
    ]
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'action', 'object_repr']
    raw_id_fields = ['user']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ['department', 'date', 'created_by', 'updated_at']
    list_filter = ['department', 'date', 'created_by', 'updated_at']
    search_fields = ['department__name', 'comment']
    raw_id_fields = ['created_by']
    readonly_fields = ['updated_at']
    date_hierarchy = 'date'


@admin.register(DailyReportPhoto)
class DailyReportPhotoAdmin(admin.ModelAdmin):
    list_display = ['daily_report', 'caption', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'daily_report__department']
    search_fields = ['caption', 'daily_report__department__name']
    raw_id_fields = ['daily_report', 'uploaded_by']
    readonly_fields = ['uploaded_at']
    date_hierarchy = 'uploaded_at'

admin.site.register(MaterialWriteOff)
admin.site.register(Project)
admin.site.register(ProjectTask)
admin.site.register(Note)
