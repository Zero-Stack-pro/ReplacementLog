import json
import os
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.timezone import localdate
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)

from .forms import (DailyReportForm, MaterialWriteOffForm, NoteForm,
                    ProjectTaskForm, ShiftFilterForm, ShiftForm, ShiftLogForm,
                    TaskFilterForm, TaskForm, TaskReportForm,
                    TaskStatusUpdateForm, UserRegistrationForm)
from .models import (ActivityLog, Attachment, DailyReport, Department,
                     Employee, MaterialWriteOff, Note, Notification, Project,
                     ProjectTask, Shift, ShiftLog, Task, TaskReport)
from .utils import log_activity, send_notification


def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Аккаунт успешно создан!')
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'shift_log/register.html', {'form': form})


@login_required
def dashboard(request):
    """Главная страница (дашборд)"""
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, 'Профиль сотрудника не найден')
        return redirect('shift_log:logout')

    # Получаем или создаём ежедневный отчёт за сегодня для отдела пользователя
    today = timezone.localdate()
    daily_report, _ = DailyReport.objects.get_or_create(
        department=employee.department,
        date=today,
        defaults={'created_by': request.user}
    )

    if request.method == 'POST' and 'daily_report_submit' in request.POST:
        form = DailyReportForm(request.POST, instance=daily_report)
        if form.is_valid():
            # Дополняем комментарий, если уже есть текст
            new_comment = form.cleaned_data['comment']
            if daily_report.comment and new_comment and new_comment != daily_report.comment:
                # Добавляем с новой строки
                daily_report.comment = f"{daily_report.comment}\n{new_comment}"
            else:
                daily_report.comment = new_comment
            daily_report.created_by = request.user
            daily_report.save()
            messages.success(request, 'Ежедневный отчёт сохранён')
            return redirect('shift_log:dashboard')
        daily_report_form = form
    else:
        daily_report_form = DailyReportForm(instance=daily_report)

    # Получаем активные задания в зависимости от роли
    if employee.position == 'admin':
        active_tasks = Task.objects.filter(
            status__in=['pending', 'in_progress']
        ).exclude(status='cancelled').select_related(
            'department', 'assigned_to', 'assigned_to__user'
        )
    elif employee.position == 'supervisor':
        active_tasks = Task.objects.filter(
            department=employee.department,
            status__in=['pending', 'in_progress']
        ).exclude(status='cancelled').select_related(
            'department', 'assigned_to', 'assigned_to__user'
        )
    else:
        active_tasks = Task.objects.filter(
            assigned_to=employee,
            status__in=['pending', 'in_progress']
        ).exclude(status='cancelled').select_related(
            'department', 'assigned_to', 'assigned_to__user'
        )

    notifications = Notification.objects.filter(
        recipient=employee,
        is_read=False
    ).order_by('-sent_at')[:5]

    # Получаем списания материалов за сегодня
    today = localdate()
    if employee.position == 'admin':
        writeoffs = MaterialWriteOff.objects.filter(created_at__date=today).select_related('department', 'created_by')
    else:
        writeoffs = MaterialWriteOff.objects.filter(department=employee.department, created_at__date=today).select_related('department', 'created_by')

    context = {
        'employee': employee,
        'active_tasks': active_tasks,
        'notifications': notifications,
        'daily_report': daily_report,
        'daily_report_form': daily_report_form,
        'writeoffs': writeoffs,
    }
    return render(
        request,
        'shift_log/dashboard.html',
        context
    )


class ShiftListView(LoginRequiredMixin, ListView):
    """Список смен"""
    model = Shift
    template_name = 'shift_log/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 20

    def get_queryset(self):
        queryset = Shift.objects.select_related(
            'shift_type', 'shift_type__department'
        ).prefetch_related('employees')
        
        # Фильтрация по правам доступа
        if hasattr(self.request.user, 'employee'):
            if self.request.user.employee.position == 'employee':
                queryset = queryset.filter(
                    employees=self.request.user.employee
                )
            elif self.request.user.employee.position == 'supervisor':
                queryset = queryset.filter(
                    shift_type__department=self.request.user.employee.department
                )

        # Применяем фильтры
        form = ShiftFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('department'):
                queryset = queryset.filter(
                    shift_type__department=form.cleaned_data['department']
                )
            if form.cleaned_data.get('shift_type'):
                queryset = queryset.filter(
                    shift_type=form.cleaned_data['shift_type']
                )
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(
                    date__gte=form.cleaned_data['date_from']
                )
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(
                    date__lte=form.cleaned_data['date_to']
                )
            if form.cleaned_data.get('is_completed') is not None:
                queryset = queryset.filter(
                    is_completed=form.cleaned_data['is_completed']
                )

        return queryset.order_by('-date', 'shift_type__start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ShiftFilterForm(self.request.GET)
        return context


class ShiftDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о смене"""
    model = Shift
    template_name = 'shift_log/shift_detail.html'
    context_object_name = 'shift'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift = self.get_object()
        
        # Проверяем права доступа
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            if employee.position == 'employee' and employee not in shift.employees.all():
                messages.error(self.request, 'У вас нет доступа к этой смене')
                return context

        # Получаем журнал смены
        try:
            shift_log = shift.shiftlog
        except ShiftLog.DoesNotExist:
            shift_log = None

        # Получаем задания смены
        tasks = Task.objects.filter(shift=shift).select_related(
            'assigned_to', 'created_by'
        )

        # Статистика задач по статусам
        tasks_stats = {
            'total': tasks.count(),
            'completed': tasks.filter(status='completed').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'pending': tasks.filter(status='pending').count(),
        }

        context.update({
            'shift_log': shift_log,
            'tasks': tasks,
            'tasks_stats': tasks_stats,
            'can_edit': self.can_edit_shift(),
        })
        return context

    def can_edit_shift(self):
        """Проверяет, может ли пользователь редактировать смену"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        employee = self.request.user.employee
        shift = self.get_object()
        
        if employee.position == 'admin':
            return True
        elif employee.position == 'supervisor':
            return shift.shift_type.department == employee.department
        else:
            return employee in shift.employees.all()


class ShiftUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование смены"""
    model = Shift
    form_class = ShiftForm
    template_name = 'shift_log/shift_form.html'
    
    def test_func(self):
        """Проверяет права доступа к редактированию смены"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        employee = self.request.user.employee
        shift = self.get_object()
        
        if employee.position == 'admin':
            return True
        elif employee.position == 'supervisor':
            return shift.shift_type.department == employee.department
        else:
            return employee in shift.employees.all()

    def get_success_url(self):
        """Возвращает URL для перенаправления после успешного обновления"""
        return reverse_lazy('shift_log:shift_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        """Обработка валидной формы"""
        response = super().form_valid(form)
        
        # Логируем активность
        log_activity(
            self.request.user,
            'update',
            'Shift',
            self.object.id,
            str(self.object)
        )
        
        messages.success(self.request, 'Смена успешно обновлена')
        return response


class TaskListView(LoginRequiredMixin, ListView):
    """Список заданий"""
    model = Task
    template_name = 'shift_log/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        queryset = Task.objects.select_related(
            'department', 'assigned_to', 'created_by'
        ).exclude(
            status__in=['completed', 'cancelled']
        )
        # Фильтрация по правам доступа
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            if employee.position == 'employee':
                queryset = queryset.filter(assigned_to=employee)
            elif employee.position == 'supervisor':
                queryset = queryset.filter(department=employee.department)
        # Применяем фильтры
        form = TaskFilterForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            if form.cleaned_data.get('department'):
                queryset = queryset.filter(
                    department=form.cleaned_data['department']
                )
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(
                    status=form.cleaned_data['status']
                )
            if form.cleaned_data.get('priority'):
                queryset = queryset.filter(
                    priority=form.cleaned_data['priority']
                )
            if form.cleaned_data.get('task_type'):
                queryset = queryset.filter(
                    task_type=form.cleaned_data['task_type']
                )
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(
                    created_at__date__gte=form.cleaned_data['date_from']
                )
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(
                    created_at__date__lte=form.cleaned_data['date_to']
                )
        return queryset.order_by(
            '-priority',
            '-created_at'
                )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = TaskFilterForm(self.request.GET, user=self.request.user)
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о задании"""
    model = Task
    template_name = 'shift_log/task_detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        
        # Проверяем права доступа
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            if (employee.position == 'employee' and 
                task.assigned_to != employee):
                messages.error(self.request, 'У вас нет доступа к этому заданию')
                return context

        # Получаем отчеты по заданию
        reports = TaskReport.objects.filter(task=task).select_related(
            'employee'
        )

        # Получаем вложения
        attachments = Attachment.objects.filter(
            attachment_type='task',
            object_id=task.id
        )

        # Добавляем форму изменения статуса
        status_form = TaskStatusUpdateForm(initial={'status': task.status})
        
        # Проверяем права на изменение статуса
        can_update_status = self.can_update_status()

        context.update({
            'reports': reports,
            'attachments': attachments,
            'can_edit_task': self.can_edit_task(),
            'status_form': status_form,
            'can_update_status': can_update_status,
        })
        return context

    def can_edit_task(self):
        """Проверяет, может ли пользователь редактировать задание"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        employee = self.request.user.employee
        task = self.get_object()
        
        # Только администраторы и руководители могут редактировать задания
        if employee.position == 'admin':
            return True
        elif employee.position == 'supervisor':
            return task.department == employee.department
        else:
            # Обычные сотрудники не могут редактировать задания
            return False
    
    def can_update_status(self):
        """Проверяет, может ли пользователь изменять статус задания"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        employee = self.request.user.employee
        task = self.get_object()
        
        # Администраторы могут изменять статус любого задания
        if employee.position == 'admin':
            return True
        
        # Руководители могут изменять статус заданий своего отдела
        if employee.position == 'supervisor' and task.department == employee.department:
            return True
        
        # Обычные сотрудники могут изменять статус только своих заданий
        if employee.position == 'employee' and task.assigned_to == employee:
            return True
        
        return False


class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание нового задания"""
    model = Task
    form_class = TaskForm
    template_name = 'shift_log/task_form.html'
    success_url = reverse_lazy('shift_log:task_list')

    def test_func(self):
        """Проверяет права на создание задания"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        employee = self.request.user.employee
        
        # Только руководители и администраторы могут создавать задачи
        if not employee.is_supervisor:
            return False
        
        # Проверяем, есть ли у сотрудника отделы для создания задач
        available_departments = employee.get_available_departments_for_tasks()
        return available_departments.exists()

    def form_valid(self, form):
        form.instance.created_by = self.request.user.employee
        response = super().form_valid(form)
        
        # Логируем активность
        log_activity(
            self.request.user,
            'create',
            'Task',
            form.instance.id,
            str(form.instance)
        )
        
        # Отправляем уведомление
        send_notification(
            form.instance.assigned_to,
            'task_assigned',
            f'Новое задание: {form.instance.title}',
            f'Вам назначено новое задание "{form.instance.title}"'
        )
        
        messages.success(self.request, 'Задание успешно создано')
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Добавляет информацию о правах доступа"""
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            context['available_departments'] = employee.get_available_departments_for_tasks()
            context['available_employees'] = employee.get_available_employees_for_assignments()
        return context


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование задания"""
    model = Task
    form_class = TaskForm
    template_name = 'shift_log/task_form.html'
    success_url = reverse_lazy('shift_log:task_list')

    def test_func(self):
        """Проверяет права на редактирование задания"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        employee = self.request.user.employee
        task = self.get_object()
        
        # Только администраторы и руководители могут редактировать задания
        if employee.position == 'admin':
            return True
        elif employee.position == 'supervisor':
            return task.department == employee.department
        else:
            # Обычные сотрудники не могут редактировать задания
            return False

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Логируем активность
        log_activity(
            self.request.user,
            'update',
            'Task',
            form.instance.id,
            str(form.instance)
        )
        
        messages.success(self.request, 'Задание успешно обновлено')
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


@login_required
def shift_log_create(request, shift_id):
    """Создание журнала смены"""
    shift = get_object_or_404(Shift, id=shift_id)
    
    # Проверяем права доступа
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'Профиль сотрудника не найден')
        return redirect('shift_list')
    
    employee = request.user.employee
    if employee not in shift.employees.all():
        messages.error(request, 'У вас нет доступа к этой смене')
        return redirect('shift_list')

    if request.method == 'POST':
        form = ShiftLogForm(request.POST)
        if form.is_valid():
            shift_log = form.save(commit=False)
            shift_log.shift = shift
            shift_log.created_by = employee
            shift_log.save()
            
            # Логируем активность
            log_activity(
                request.user,
                'create',
                'ShiftLog',
                shift_log.id,
                str(shift_log)
            )
            
            messages.success(request, 'Журнал смены создан')
            return redirect('shift_detail', pk=shift_id)
    else:
        form = ShiftLogForm()

    return render(request, 'shift_log/shift_log_form.html', {
        'form': form,
        'shift': shift
    })


@login_required
def task_report_create(request, task_id):
    """Создание отчета по заданию"""
    task = get_object_or_404(Task, id=task_id)
    
    # Проверяем права доступа
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'Профиль сотрудника не найден')
        return redirect('task_list')
    
    employee = request.user.employee
    if task.assigned_to != employee:
        messages.error(request, 'У вас нет доступа к этому заданию')
        return redirect('task_list')

    if request.method == 'POST':
        form = TaskReportForm(request.POST)
        if form.is_valid():
            # Получаем или создаем журнал смены
            shift_log, created = ShiftLog.objects.get_or_create(
                shift=task.shift,
                defaults={'created_by': employee}
            )
            
            report = form.save(commit=False)
            report.task = task
            report.shift_log = shift_log
            report.employee = employee
            report.save()
            
            # Обновляем статус задания
            task.status = form.cleaned_data['status']
            if form.cleaned_data['status'] == 'completed':
                task.completed_at = timezone.now()
            task.save()
            
            # Логируем активность
            log_activity(
                request.user,
                'create',
                'TaskReport',
                report.id,
                str(report)
            )
            
            messages.success(request, 'Отчет создан')
            return redirect('task_detail', pk=task_id)
    else:
        form = TaskReportForm()

    return render(request, 'shift_log/task_report_form.html', {
        'form': form,
        'task': task
    })


@login_required
def upload_attachment(request):
    """Загрузка вложения"""
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.uploaded_by = request.user.employee
            attachment.filename = request.FILES['file'].name
            attachment.content_type = request.FILES['file'].content_type
            attachment.file_size = request.FILES['file'].size
            
            # Получаем тип вложения и ID объекта из POST данных
            attachment.attachment_type = request.POST.get('attachment_type', 'task')
            attachment.object_id = request.POST.get('object_id')
            
            attachment.save()
            
            return JsonResponse({
                'success': True,
                'attachment_id': attachment.id,
                'filename': attachment.filename,
                'file_size': attachment.file_size,
                'uploaded_by': attachment.uploaded_by.user.get_full_name() or attachment.uploaded_by.user.username
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def notifications_list(request):
    """Список уведомлений"""
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'Профиль сотрудника не найден')
        return redirect('shift_log:dashboard')
    
    notifications = Notification.objects.filter(
        recipient=request.user.employee
    ).order_by('-sent_at')
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'shift_log/notifications_list.html', {
        'notifications': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages()
    })


@login_required
def mark_notification_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    print(f"DEBUG: mark_notification_read called with notification_id={notification_id}")
    print(f"DEBUG: user={request.user}, employee={getattr(request.user, 'employee', None)}")
    
    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user.employee
        )
        print(f"DEBUG: notification found: {notification}")
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        print(f"DEBUG: notification marked as read")
        
        # Проверяем, является ли это AJAX-запросом
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            # Обычный POST-запрос - перенаправляем обратно
            messages.success(request, 'Уведомление отмечено как прочитанное')
            return redirect('shift_log:dashboard')
            
    except Exception as e:
        print(f"DEBUG: error in mark_notification_read: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            messages.error(request, f'Ошибка при отметке уведомления: {str(e)}')
            return redirect('shift_log:dashboard')


@login_required
def mark_all_notifications_read(request):
    """Отметить все уведомления как прочитанные"""
    if not hasattr(request.user, 'employee'):
        return JsonResponse({'success': False, 'error': 'Профиль сотрудника не найден'})
    
    if request.method == 'POST':
        try:
            # Пытаемся получить данные из JSON
            try:
                data = json.loads(request.body)
                notification_ids = data.get('notification_ids', [])
            except json.JSONDecodeError:
                notification_ids = []
            
            # Если переданы конкретные ID, отмечаем только их
            if notification_ids:
                notifications = Notification.objects.filter(
                    id__in=notification_ids,
                    recipient=request.user.employee,
                    is_read=False
                )
            else:
                # Иначе отмечаем все непрочитанные уведомления пользователя
                notifications = Notification.objects.filter(
                    recipient=request.user.employee,
                    is_read=False
                )
            
            # Отмечаем их как прочитанные
            count = notifications.update(
                is_read=True,
                read_at=timezone.now()
            )
            
            print(f"API: Отмечено {count} уведомлений как прочитанные для {request.user.employee.user.username}")
            
            response = JsonResponse({
                'success': True,
                'count': count,
                'marked_ids': list(notifications.values_list('id', flat=True))
            })
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})


@csrf_exempt
@login_required
def api_task_status_update(request, task_id):
    """API для обновления статуса задания"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task = get_object_or_404(Task, id=task_id)
            
            # Проверяем права доступа
            if not hasattr(request.user, 'employee'):
                return JsonResponse({'success': False, 'error': 'Unauthorized'})
            
            employee = request.user.employee
            if task.assigned_to != employee:
                return JsonResponse({'success': False, 'error': 'Access denied'})
            
            new_status = data.get('status')
            if new_status in dict(Task.STATUS_CHOICES):
                task.status = new_status
                if new_status == 'completed':
                    task.completed_at = timezone.now()
                task.save()
                
                # Логируем активность
                log_activity(
                    request.user,
                    'update_status',
                    'Task',
                    task.id,
                    f'Status changed to {new_status}'
                )
                
                # Создаем уведомления для заинтересованных лиц
                from .utils import send_notification

                # Получаем отображаемые названия статусов
                status_choices = dict(Task.STATUS_CHOICES)
                new_status_display = status_choices.get(new_status, new_status)
                
                # Уведомление для создателя задачи
                if task.created_by != employee:
                    send_notification(
                        task.created_by,
                        'task_completed' if new_status == 'completed' else 'task_assigned',
                        f'Статус задачи изменен: {task.title}',
                        f'Статус задачи "{task.title}" изменен на "{new_status_display}"'
                    )
                
                            # Уведомление для руководителя отдела (если он не тот, кто изменил статус)
            department_supervisor = Employee.objects.filter(
                department=task.department,
                position='supervisor',
                is_active=True
            ).first()
            if department_supervisor and department_supervisor != employee:
                send_notification(
                    department_supervisor,
                    'task_completed' if new_status == 'completed' else 'task_assigned',
                    f'Статус задачи изменен: {task.title}',
                    f'Статус задачи "{task.title}" в отделе {task.department.name} изменен на "{new_status_display}"'
                )
                
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid status'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def get_shifts_by_department(request):
    """AJAX-эндпоинт для получения смен по отделу"""
    department_id = request.GET.get('department_id')
    
    if not department_id:
        return JsonResponse({'shifts': []})
    
    try:
        # Получаем смены для указанного отдела
        shifts = Shift.objects.filter(
            shift_type__department_id=department_id
        ).select_related('shift_type').order_by('date', 'shift_type__start_time')
        
        # Формируем данные для ответа
        shifts_data = []
        for shift in shifts:
            shifts_data.append({
                'id': shift.id,
                'name': f"{shift.date} - {shift.shift_type.name} ({shift.shift_type.start_time} - {shift.shift_type.end_time})"
            })
        
        return JsonResponse({'shifts': shifts_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def get_employees_by_department(request):
    """AJAX-эндпоинт для получения сотрудников по отделу"""
    department_id = request.GET.get('department_id')
    
    if not department_id:
        return JsonResponse({'employees': []})
    
    try:
        # Проверяем права доступа
        if not hasattr(request.user, 'employee'):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        employee = request.user.employee
        
        # Получаем сотрудников для указанного отдела
        employees = Employee.objects.filter(
            department_id=department_id,
            is_active=True
        ).select_related('user', 'department').order_by('user__first_name', 'user__last_name')
        
        # Проверяем права на назначение задач
        if not employee.is_admin:
            if employee.is_supervisor:
                # Руководители могут назначать задачи только сотрудникам своего отдела
                if str(employee.department.id) != department_id:
                    return JsonResponse({'error': 'Access denied'}, status=403)
            else:
                # Обычные сотрудники могут видеть сотрудников только своего отдела
                if str(employee.department.id) != department_id:
                    return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Формируем данные для ответа
        employees_data = []
        for emp in employees:
            employees_data.append({
                'id': emp.id,
                'name': f"{emp.user.get_full_name() or emp.user.username} ({emp.department.name})",
                'position': emp.position or 'Не указана'
            })
        
        return JsonResponse({'employees': employees_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


class TaskStatusUpdateView(LoginRequiredMixin, View):
    """Изменение статуса задания"""
    
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        employee = request.user.employee
        
        # Проверяем права на изменение статуса
        if not self.can_update_status(employee, task):
            messages.error(request, 'У вас нет прав для изменения статуса этого задания')
            return redirect('shift_log:task_detail', pk=pk)
        
        form = TaskStatusUpdateForm(request.POST)
        if form.is_valid():
            old_status = task.status
            new_status = form.cleaned_data['status']
            comment = form.cleaned_data.get('comment', '')
            
            # Обновляем статус
            task.status = new_status
            
            # Если статус меняется на "завершено", устанавливаем время завершения
            if new_status == 'completed' and old_status != 'completed':
                task.completed_at = timezone.now()
            
            task.save()
            
            # Создаем запись в истории изменений
            # Получаем отображаемые названия статусов
            status_choices = dict(Task.STATUS_CHOICES)
            old_status_display = status_choices.get(old_status, old_status)
            new_status_display = status_choices.get(new_status, new_status)
            
            action = f'Статус изменен с "{old_status_display}" на "{new_status_display}"'
            if comment:
                action += f': {comment}'
            
            ActivityLog.objects.create(
                user=request.user,
                action='status_changed',
                model_name='Task',
                object_id=task.id,
                object_repr=str(task),
                description=action,
                changes={
                    'old_status': old_status,
                    'new_status': new_status,
                    'comment': comment
                }
            )
            
            # Создаем уведомления для заинтересованных лиц
            from .utils import send_notification

            # Уведомление для создателя задачи
            if task.created_by != employee:
                send_notification(
                    task.created_by,
                    'task_completed' if new_status == 'completed' else 'task_assigned',
                    f'Статус задачи изменен: {task.title}',
                    f'Статус задачи "{task.title}" изменен с "{old_status_display}" на "{new_status_display}"{f" с комментарием: {comment}" if comment else ""}'
                )
            
            # Уведомление для назначенного сотрудника (если он не тот, кто изменил статус)
            if task.assigned_to != employee:
                send_notification(
                    task.assigned_to,
                    'task_completed' if new_status == 'completed' else 'task_assigned',
                    f'Статус задачи изменен: {task.title}',
                    f'Статус задачи "{task.title}" изменен с "{old_status_display}" на "{new_status_display}"{f" с комментарием: {comment}" if comment else ""}'
                )
            
            # Уведомление для руководителя отдела (если он не тот, кто изменил статус)
            department_supervisor = Employee.objects.filter(
                department=task.department,
                position='supervisor',
                is_active=True
            ).first()
            if department_supervisor and department_supervisor != employee:
                send_notification(
                    department_supervisor,
                    'task_completed' if new_status == 'completed' else 'task_assigned',
                    f'Статус задачи изменен: {task.title}',
                    f'Статус задачи "{task.title}" в отделе {task.department.name} изменен с "{old_status_display}" на "{new_status_display}"{f" с комментарием: {comment}" if comment else ""}'
                )
            
            messages.success(request, 'Статус задания успешно обновлен')
            return redirect('shift_log:task_detail', pk=pk)
        else:
            messages.error(request, 'Ошибка при обновлении статуса')
            return redirect('shift_log:task_detail', pk=pk)
    
    def can_update_status(self, employee, task):
        """Проверяет права на изменение статуса задания"""
        # Администраторы могут изменять статус любого задания
        if employee.position == 'admin':
            return True
        
        # Руководители могут изменять статус заданий своего отдела
        if employee.position == 'supervisor' and task.department == employee.department:
            return True
        
        # Обычные сотрудники могут изменять статус только своих заданий
        if employee.position == 'employee' and task.assigned_to == employee:
            return True
        
        return False


@login_required
def api_notifications_count(request):
    """API для получения количества непрочитанных уведомлений"""
    try:
        employee = request.user.employee
        count = Notification.objects.filter(
            recipient=employee,
            is_read=False
        ).count()
        
        print(f"API: Количество непрочитанных уведомлений для {employee.user.username}: {count}")
        response = JsonResponse({'count': count})
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    except Exception as e:
        print(f"API: Ошибка при подсчете уведомлений: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_notifications_recent(request):
    """API для получения последних непрочитанных уведомлений"""
    try:
        employee = request.user.employee
        notifications = Notification.objects.filter(
            recipient=employee,
            is_read=False
        ).order_by('-sent_at')[:5]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'is_read': notification.is_read,
                'sent_at': notification.sent_at.strftime('%d.%m.%Y %H:%M')
            })
        
        response = JsonResponse({'notifications': notifications_data})
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def delete_attachment(request, attachment_id):
    """Удаление вложения"""
    try:
        attachment = get_object_or_404(Attachment, id=attachment_id)
        
        # Проверяем права доступа
        if not hasattr(request.user, 'employee'):
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
        
        employee = request.user.employee
        
        # Администраторы могут удалять любые вложения
        if employee.position == 'admin':
            pass
        # Руководители могут удалять вложения заданий своего отдела
        elif employee.position == 'supervisor':
            if attachment.attachment_type == 'task':
                task = get_object_or_404(Task, id=attachment.object_id)
                if task.department != employee.department:
                    return JsonResponse({'success': False, 'error': 'Access denied'})
            else:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        # Обычные сотрудники могут удалять только свои вложения
        elif employee.position == 'employee':
            if attachment.uploaded_by != employee:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        else:
            return JsonResponse({'success': False, 'error': 'Access denied'})
        
        # Удаляем файл с диска
        if attachment.file:
            if os.path.exists(attachment.file.path):
                os.remove(attachment.file.path)
        
        # Удаляем запись из базы данных
        attachment.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def download_attachment(request, attachment_id):
    """Скачивание вложения"""
    try:
        attachment = get_object_or_404(Attachment, id=attachment_id)
        
        # Проверяем права доступа
        if not hasattr(request.user, 'employee'):
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
        
        employee = request.user.employee
        
        # Администраторы могут скачивать любые вложения
        if employee.position == 'admin':
            pass
        # Руководители могут скачивать вложения заданий своего отдела
        elif employee.position == 'supervisor':
            if attachment.attachment_type == 'task':
                task = get_object_or_404(Task, id=attachment.object_id)
                if task.department != employee.department:
                    return JsonResponse({'success': False, 'error': 'Access denied'})
            else:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        # Обычные сотрудники могут скачивать вложения заданий, к которым у них есть доступ
        elif employee.position == 'employee':
            if attachment.attachment_type == 'task':
                task = get_object_or_404(Task, id=attachment.object_id)
                if task.assigned_to != employee and task.created_by != employee:
                    return JsonResponse({'success': False, 'error': 'Access denied'})
            else:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        else:
            return JsonResponse({'success': False, 'error': 'Access denied'})
        
        # Отправляем файл
        with open(attachment.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=attachment.content_type)
            response['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
            return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def reports_list(request):
    """Список заданий с историей изменений за выбранный период"""
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'Профиль сотрудника не найден')
        return redirect('shift_log:dashboard')
    
    employee = request.user.employee
    
    # Устанавливаем значения по умолчанию (вчерашняя дата)
    yesterday = (timezone.now() - timedelta(days=1)).date()
    default_date_from = yesterday.strftime('%Y-%m-%d')
    default_date_to = yesterday.strftime('%Y-%m-%d')
    
    # Фильтрация
    department_filter = request.GET.get('department')
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from', default_date_from)
    date_to = request.GET.get('date_to', default_date_to)
    
    # Получаем задания в зависимости от роли пользователя
    if employee.position == 'admin':
        # Администратор видит все задания
        tasks = Task.objects.exclude(status='cancelled').select_related(
            'department', 'assigned_to', 'assigned_to__user', 'created_by', 'created_by__user'
        ).prefetch_related('taskreport_set').order_by('-created_at')
    elif employee.position == 'supervisor':
        # Руководитель видит задания только своего отдела
        tasks = Task.objects.filter(
            department=employee.department
        ).exclude(status='cancelled').select_related(
            'department', 'assigned_to', 'assigned_to__user', 'created_by', 'created_by__user'
        ).prefetch_related('taskreport_set').order_by('-created_at')
    else:
        # Сотрудник видит только свои задания
        tasks = Task.objects.filter(
            assigned_to=employee
        ).exclude(status='cancelled').select_related(
            'department', 'assigned_to', 'assigned_to__user', 'created_by', 'created_by__user'
        ).prefetch_related('taskreport_set').order_by('-created_at')
    
    # Для руководителей автоматически устанавливаем фильтр по их отделу, если не указан другой
    if employee.position == 'supervisor' and not department_filter:
        department_filter = str(employee.department.id)
    
    # Применяем фильтры
    if department_filter and employee.position in ['admin', 'supervisor']:
        tasks = tasks.filter(department_id=department_filter)
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Всегда применяем фильтр по датам
    if date_from:
        tasks = tasks.filter(created_at__date__gte=date_from)
    
    if date_to:
        tasks = tasks.filter(created_at__date__lte=date_to)
    
    # Пагинация
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем доступные отделы для фильтрации
    if employee.position == 'admin':
        departments = Department.objects.all()
    elif employee.position == 'supervisor':
        departments = Department.objects.filter(id=employee.department.id)
    else:
        departments = Department.objects.none()
    
    # Статистика
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    pending_tasks = tasks.filter(status='pending').count()
    
    context = {
        'tasks': page_obj,
        'departments': departments,
        'status_choices': Task.STATUS_CHOICES,
        'employee': employee,
        'filters': {
            'department': department_filter,
            'status': status_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
        'stats': {
            'total': total_tasks,
            'completed': completed_tasks,
            'in_progress': in_progress_tasks,
            'pending': pending_tasks,
        }
    }
    
    return render(
        request,
        'shift_log/reports_list.html',
        context
    )


@login_required
def update_task_comment(request, task_id):
    """Обновление комментария к заданию"""
    task = get_object_or_404(Task, id=task_id)
    
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'Профиль сотрудника не найден')
        return redirect('shift_log:dashboard')
    
    employee = request.user.employee
    
    # Проверяем права на редактирование
    if not (employee.position == 'admin' or 
            employee.department == task.department or 
            task.assigned_to == employee or 
            task.created_by == employee):
        messages.error(request, 'У вас нет прав для редактирования этого задания')
        return redirect('shift_log:task_list')
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()
        
        # Сохраняем старый комментарий для логирования
        old_comment = task.comment
        
        # Обновляем комментарий
        task.comment = comment
        task.save()
        
        # Логируем изменение
        if old_comment != comment:
            if comment:
                description = f"Комментарий обновлен: {comment[:100]}{'...' if len(comment) > 100 else ''}"
            else:
                description = "Комментарий удален"
            
            log_activity(
                user=request.user,
                action='updated',
                model_name='Task',
                object_id=task.id,
                object_repr=task.title,
                description=description,
                changes={'comment': {'old': old_comment, 'new': comment}}
            )
            
            messages.success(request, 'Комментарий успешно обновлен')
        else:
            messages.info(request, 'Комментарий не изменился')
        
        return redirect('shift_log:task_detail', pk=task_id)
    
    # GET запрос - показываем форму
    return render(request, 'shift_log/task_comment_form.html', {
        'task': task,
        'current_comment': task.comment
    })


@login_required
def api_task_history(request, task_id):
    """API для получения истории изменений задания"""
    task = get_object_or_404(Task, pk=task_id)
    
    # Проверяем права доступа
    if not hasattr(request.user, 'employee'):
        return JsonResponse({'success': False, 'error': 'Профиль сотрудника не найден'})
    
    employee = request.user.employee
    
    # Проверяем, может ли пользователь просматривать задание
    can_view = False
    if employee.position == 'admin':
        can_view = True
    elif employee.position == 'supervisor':
        can_view = task.department == employee.department
    else:
        can_view = task.assigned_to == employee or task.created_by == employee
    
    if not can_view:
        return JsonResponse({'success': False, 'error': 'У вас нет прав для просмотра этого задания'})
    
    try:
        # Получаем историю изменений
        activity_logs = ActivityLog.objects.filter(
            model_name='Task',
            object_id=task.id
        ).select_related('user').order_by('-timestamp')
        
        history = []
        for log in activity_logs:
            # Получаем отображаемые названия статусов
            status_choices = dict(Task.STATUS_CHOICES)
            
            # Обрабатываем изменения для отображения
            processed_changes = log.changes
            if processed_changes:
                if 'old_status' in processed_changes:
                    processed_changes['old_status'] = status_choices.get(
                        processed_changes['old_status'], 
                        processed_changes['old_status']
                    )
                if 'new_status' in processed_changes:
                    processed_changes['new_status'] = status_choices.get(
                        processed_changes['new_status'], 
                        processed_changes['new_status']
                    )
            
            history.append({
                'id': log.id,
                'user_name': log.user.get_full_name() or log.user.username,
                'action': log.get_action_display(),
                'timestamp': log.timestamp.strftime('%d.%m.%Y %H:%M'),
                'description': log.description,
                'changes': processed_changes
            })
        
        return JsonResponse({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def daily_reports_list(request):
    """Список ежедневных отчётов по отделу (или всем отделам для администратора)"""
    employee = request.user.employee
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    reports = DailyReport.objects.all()
    if employee.position == 'admin':
        # Администратор видит все
        if request.GET.get('department'):
            reports = reports.filter(department_id=request.GET['department'])
    else:
        # Сотрудник и руководитель — только свой отдел
        reports = reports.filter(department=employee.department)

    if date_from:
        reports = reports.filter(date__gte=date_from)
    if date_to:
        reports = reports.filter(date__lte=date_to)

    reports = reports.select_related('department', 'created_by').order_by('-date')

    # Для фильтрации по отделу (только для админа)
    departments = Department.objects.all() if employee.position == 'admin' else None

    context = {
        'reports': reports,
        'departments': departments,
        'employee': employee,
        'date_from': date_from,
        'date_to': date_to,
        'selected_department': request.GET.get('department', ''),
    }
    return render(request, 'shift_log/daily_reports_list.html', context)


class MaterialWriteOffListView(LoginRequiredMixin, ListView):
    model = MaterialWriteOff
    template_name = 'shift_log/material_writeoff_list.html'
    context_object_name = 'writeoffs'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        from datetime import timedelta

        from django.utils.timezone import localdate
        yesterday = localdate() - timedelta(days=1)
        date_from = self.request.GET.get('date_from', yesterday.strftime('%Y-%m-%d'))
        date_to = self.request.GET.get('date_to', yesterday.strftime('%Y-%m-%d'))
        department_id = self.request.GET.get('department')
        created_by_id = self.request.GET.get('created_by')

        qs = MaterialWriteOff.objects.all().select_related('department', 'created_by')
        if hasattr(user, 'employee'):
            employee = user.employee
            if employee.position == 'admin':
                # Фильтрация по отделу для админа
                if department_id:
                    qs = qs.filter(department_id=department_id)
            else:
                # Только свой отдел
                qs = qs.filter(department=employee.department)
            # Фильтрация по сотруднику
            if created_by_id:
                qs = qs.filter(created_by_id=created_by_id)
        # Фильтрация по дате
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        employee = getattr(user, 'employee', None)
        # Для фильтрации по отделу и сотруднику
        if employee and employee.position == 'admin':
            context['departments'] = Department.objects.all()
        elif employee:
            context['departments'] = Department.objects.filter(id=employee.department.id)
        else:
            context['departments'] = Department.objects.none()
        # Список сотрудников для фильтра
        if employee and employee.position == 'admin':
            context['employees'] = Employee.objects.all()
        elif employee:
            context['employees'] = Employee.objects.filter(department=employee.department)
        else:
            context['employees'] = Employee.objects.none()
        context['employee'] = employee
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_created_by'] = self.request.GET.get('created_by', '')
        return context


class MaterialWriteOffCreateView(LoginRequiredMixin, CreateView):
    model = MaterialWriteOff
    form_class = MaterialWriteOffForm
    template_name = 'shift_log/material_writeoff_form.html'
    success_url = reverse_lazy('shift_log:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        if hasattr(user, 'employee'):
            employee = user.employee
            form.instance.created_by = employee
            if not employee.is_admin:
                form.instance.department = employee.department
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.request.user.employee
        return context


class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'shift_log/note_list.html'
    context_object_name = 'notes'
    paginate_by = 20

    def get_queryset(self):
        return Note.objects.filter(employee=self.request.user.employee).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.request.user.employee
        return context

class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    form_class = NoteForm
    template_name = 'shift_log/note_form.html'
    success_url = reverse_lazy('shift_log:note_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        messages.success(self.request, 'Заметка успешно добавлена!')
        return super().form_valid(form)

class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = 'shift_log/note_form.html'
    success_url = reverse_lazy('shift_log:note_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def get_queryset(self):
        return Note.objects.filter(employee=self.request.user.employee)

    def form_valid(self, form):
        messages.success(self.request, 'Заметка обновлена!')
        return super().form_valid(form)

class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = 'shift_log/note_confirm_delete.html'
    success_url = reverse_lazy('shift_log:note_list')

    def get_queryset(self):
        return Note.objects.filter(employee=self.request.user.employee)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Заметка удалена!')
        return super().delete(request, *args, **kwargs)

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'shift_log/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        return Project.objects.filter(employee=self.request.user.employee).order_by('name')

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        context = super().get_context_data(**kwargs)
        context['employee'] = self.request.user.employee
        # Для каждого проекта — незавершённые задачи
        projects = context['projects']
        project_tasks = {}
        project_status_color = {}
        now = timezone.now()
        for project in projects:
            tasks = project.tasks.filter(status__in=['new', 'in_progress'])
            project_tasks[project.id] = tasks
            # Цветовая политика:
            # danger — есть просроченные (in_progress/new и due_date < now)
            # warning — есть в работе (in_progress)
            # info — есть только новые (new)
            # success — нет незавершённых задач
            overdue = tasks.filter(due_date__lt=now, status__in=['new', 'in_progress']).exists()
            in_progress = tasks.filter(status='in_progress').exists()
            only_new = tasks.filter(status='new').exists() and not in_progress and not overdue
            if overdue:
                color = 'danger'
            elif in_progress:
                color = 'warning'
            elif only_new:
                color = 'info'
            else:
                color = 'success'
            project_status_color[project.id] = color
        context['project_tasks'] = project_tasks
        context['project_status_color'] = project_status_color
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ['name']
    template_name = 'shift_log/project_form.html'
    success_url = reverse_lazy('shift_log:project_list')

    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        return super().form_valid(form)

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ['name']
    template_name = 'shift_log/project_form.html'
    success_url = reverse_lazy('shift_log:project_list')

    def get_queryset(self):
        return Project.objects.filter(employee=self.request.user.employee)

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'shift_log/project_confirm_delete.html'
    success_url = reverse_lazy('shift_log:project_list')

    def get_queryset(self):
        return Project.objects.filter(employee=self.request.user.employee)

class ProjectTaskListView(LoginRequiredMixin, ListView):
    model = ProjectTask
    template_name = 'shift_log/projecttask_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return ProjectTask.objects.filter(project__id=project_id, employee=self.request.user.employee).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, id=self.kwargs.get('project_id'), employee=self.request.user.employee)
        context['project'] = project
        context['employee'] = self.request.user.employee
        return context

class ProjectTaskCreateView(LoginRequiredMixin, CreateView):
    model = ProjectTask
    form_class = ProjectTaskForm
    template_name = 'shift_log/projecttask_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        project_id = self.kwargs.get('project_id')
        if project_id:
            project = get_object_or_404(Project, id=project_id, employee=self.request.user.employee)
            kwargs['project_instance'] = project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs.get('project_id')
        if project_id:
            context['current_project'] = get_object_or_404(Project, id=project_id, employee=self.request.user.employee)
        return context

    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        project_id = self.kwargs.get('project_id')
        form.instance.project = get_object_or_404(Project, id=project_id, employee=self.request.user.employee)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('shift_log:project_list')

class ProjectTaskUpdateView(LoginRequiredMixin, UpdateView):
    model = ProjectTask
    form_class = ProjectTaskForm
    template_name = 'shift_log/projecttask_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return ProjectTask.objects.filter(employee=self.request.user.employee)

    def get_success_url(self):
        return reverse('shift_log:projecttask_list', kwargs={'project_id': self.object.project.id})

class ProjectTaskDeleteView(LoginRequiredMixin, DeleteView):
    model = ProjectTask
    template_name = 'shift_log/projecttask_confirm_delete.html'

    def get_queryset(self):
        return ProjectTask.objects.filter(employee=self.request.user.employee)

    def get_success_url(self):
        return reverse('shift_log:projecttask_list', kwargs={'project_id': self.object.project.id})
