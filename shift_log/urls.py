from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .views import (MaterialWriteOffCreateView, MaterialWriteOffListView,
                    NoteCreateView, NoteDeleteView, NoteListView,
                    NoteUpdateView, ProjectCreateView, ProjectDeleteView,
                    ProjectListView, ProjectTaskCreateView,
                    ProjectTaskDeleteView, ProjectTaskListView,
                    ProjectTaskUpdateView, ProjectUpdateView)

app_name = 'shift_log'

urlpatterns = [
    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='shift_log/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Главная страница
    path('', views.dashboard, name='dashboard'),
    

    
    # Задания
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/status/', views.TaskStatusUpdateView.as_view(), name='task_status_update'),
    path('tasks/<int:task_id>/comment/', views.update_task_comment, name='update_task_comment'),
    path('tasks/<int:task_id>/report/create/', views.task_report_create, name='task_report_create'),
    
    # Отчеты
    path('reports/', views.reports_list, name='reports_list'),
    
    # Ежедневные отчёты
    path('daily-reports/', views.daily_reports_list, name='daily_reports_list'),
    
    # API
    path('api/tasks/<int:task_id>/status/', views.api_task_status_update, name='api_task_status_update'),
    path('api/tasks/<int:task_id>/history/', views.api_task_history, name='api_task_history'),
    path('api/upload-attachment/', views.upload_attachment, name='upload_attachment'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    path('attachments/<int:attachment_id>/download/', views.download_attachment, name='download_attachment'),

    path('api/get-employees-by-department/', views.get_employees_by_department, name='get_employees_by_department'),
    
    # Уведомления
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # API уведомлений
    path('api/notifications/count/', views.api_notifications_count, name='api_notifications_count'),
    path('api/notifications/recent/', views.api_notifications_recent, name='api_notifications_recent'),
]

urlpatterns += [
    path('materials/writeoff/', MaterialWriteOffListView.as_view(), name='material_writeoff_list'),
    path('materials/writeoff/create/', MaterialWriteOffCreateView.as_view(), name='material_writeoff_create'),
] 

urlpatterns += [
    path('notes/', NoteListView.as_view(), name='note_list'),
    path('notes/create/', NoteCreateView.as_view(), name='note_create'),
    path('notes/<int:pk>/edit/', NoteUpdateView.as_view(), name='note_edit'),
    path('notes/<int:pk>/delete/', NoteDeleteView.as_view(), name='note_delete'),
] 

urlpatterns += [
    path('projects/', ProjectListView.as_view(), name='project_list'),
    path('projects/create/', ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project_delete'),
    path('projects/<int:project_id>/tasks/', ProjectTaskListView.as_view(), name='projecttask_list'),
    path('projects/<int:project_id>/tasks/create/', ProjectTaskCreateView.as_view(), name='projecttask_create'),
    path('projecttasks/<int:pk>/edit/', ProjectTaskUpdateView.as_view(), name='projecttask_edit'),
    path('projecttasks/<int:pk>/delete/', ProjectTaskDeleteView.as_view(), name='projecttask_delete'),
] 