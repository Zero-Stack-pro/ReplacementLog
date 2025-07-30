from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (Attachment, DailyReport, Department, Employee,
                     MaterialWriteOff, Note, Project, ProjectTask, Shift,
                     ShiftLog, ShiftType, Task, TaskReport)


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class EmployeeForm(forms.ModelForm):
    """Форма сотрудника"""
    class Meta:
        model = Employee
        fields = ['department', 'position', 'phone', 'telegram_id', 'is_active']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'telegram_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DepartmentForm(forms.ModelForm):
    """Форма отдела"""
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ShiftTypeForm(forms.ModelForm):
    """Форма типа смены"""
    class Meta:
        model = ShiftType
        fields = [
            'name', 'department', 'description', 'start_time', 'end_time',
            'periodicity', 'duration_hours', 'is_overnight', 'working_days',
            'day_of_month', 'custom_interval_days', 'color', 'is_active',
            'start_date', 'end_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'working_days': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1,2,3,4,5 (1-Пн, 2-Вт, 3-Ср, 4-Чт, 5-Пт, 6-Сб, 7-Вс)'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '24'
            }),
            'day_of_month': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '31'
            }),
            'custom_interval_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'employee'):
            employee = user.employee
            
            # Ограничиваем выбор отдела в зависимости от роли
            if not employee.is_admin:
                if employee.is_supervisor:
                    # Руководители могут создавать типы смен только для своего отдела
                    self.fields['department'].queryset = Department.objects.filter(
                        id=employee.department.id
                    )
                else:
                    # Обычные сотрудники не могут создавать типы смен
                    self.fields['department'].queryset = Department.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Валидация рабочих дней
        working_days = cleaned_data.get('working_days', '')
        periodicity = cleaned_data.get('periodicity', '')
        
        if working_days and periodicity in ['weekly', 'biweekly']:
            try:
                working_list = [int(day.strip()) for day in working_days.split(',') if day.strip().isdigit()]
                
                # Проверяем диапазон дней (1-7)
                invalid_days = [day for day in working_list if day < 1 or day > 7]
                if invalid_days:
                    raise forms.ValidationError(
                        f'Неверные номера дней: {invalid_days}. Используйте числа от 1 до 7'
                    )
                    
            except ValueError:
                raise forms.ValidationError(
                    'Неверный формат дней. Используйте числа через запятую (например: 1,2,3,4,5)'
                )
        
        # Валидация дня месяца
        day_of_month = cleaned_data.get('day_of_month')
        if day_of_month and periodicity == 'monthly':
            if day_of_month < 1 or day_of_month > 31:
                raise forms.ValidationError(
                    'День месяца должен быть от 1 до 31'
                )
        
        # Валидация пользовательского интервала
        custom_interval = cleaned_data.get('custom_interval_days')
        if custom_interval and periodicity == 'custom':
            if custom_interval < 1:
                raise forms.ValidationError(
                    'Интервал должен быть больше 0'
                )
        
        # Валидация дат
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError(
                'Дата окончания должна быть позже даты начала'
            )
        
        return cleaned_data


class ShiftForm(forms.ModelForm):
    """Форма смены"""
    class Meta:
        model = Shift
        fields = ['date', 'shift_type']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class TaskForm(forms.ModelForm):
    """Форма задания"""
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'comment', 'department', 'assigned_to',
            'priority', 'task_type', 'task_scope', 'due_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Дополнительные комментарии к заданию...'}),
            'due_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.user = user
        if user and hasattr(user, 'employee'):
            employee = user.employee
            # Определяем уровень пользователя
            role_order = {'employee': 1, 'supervisor': 2, 'admin': 3}
            my_role = getattr(employee, 'position', 'employee')
            my_level = role_order.get(my_role, 1)
            
            if not employee.is_admin:
                self.fields['department'].widget = forms.HiddenInput()
                self.fields['department'].initial = employee.department
                self.fields['department'].queryset = Department.objects.filter(
                    id=employee.department.id
                )
            
            # Ограничиваем выбор сотрудников для назначения
            if not employee.is_admin:
                if employee.is_supervisor:
                    # Руководители могут назначать задачи сотрудникам своего отдела
                    self.fields['assigned_to'].queryset = Employee.objects.filter(
                        department=employee.department,
                        is_active=True
                    ).select_related('user', 'department').order_by('user__first_name', 'user__last_name')
                else:
                    # Обычные сотрудники могут назначать задачи только себе
                    self.fields['assigned_to'].queryset = Employee.objects.filter(
                        id=employee.id,
                        is_active=True
                    ).select_related('user', 'department')
            else:
                # Для администраторов определяем отдел из данных формы
                dept = None
                
                # Сначала проверяем данные POST (при ошибке валидации)
                if self.data.get('department'):
                    try:
                        dept = Department.objects.get(pk=self.data.get('department'))
                    except (Department.DoesNotExist, ValueError):
                        dept = None
                
                # Если нет в POST, проверяем initial данные
                if not dept and self.initial.get('department'):
                    dept = self.initial.get('department')
                
                # Если нет в initial, проверяем instance (для редактирования)
                if not dept and self.instance and self.instance.pk:
                    dept = self.instance.department
                
                # Устанавливаем queryset для assigned_to
                if dept:
                    self.fields['assigned_to'].queryset = Employee.objects.filter(
                        department=dept,
                        is_active=True
                    ).select_related('user', 'department').order_by('user__first_name', 'user__last_name')
                else:
                    # Если отдел не определен, показываем всех сотрудников
                    self.fields['assigned_to'].queryset = Employee.objects.filter(
                        is_active=True
                    ).select_related('user', 'department').order_by('user__first_name', 'user__last_name')
            
            # Добавляем JavaScript для динамического изменения поля assigned_to
            self.fields['task_scope'].widget.attrs.update({
                'class': 'form-select',
                'onchange': 'toggleAssignedToField()'
            })
            
            # Делаем поле assigned_to необязательным для общих задач
            self.fields['assigned_to'].required = False

    def clean(self):
        cleaned_data = super().clean()
        user = getattr(self, 'user', None)
        if user and hasattr(user, 'employee'):
            employee = user.employee
            role_order = {'employee': 1, 'supervisor': 2, 'admin': 3}
            my_role = getattr(employee, 'position', 'employee')
            my_level = role_order.get(my_role, 1)
            if not employee.is_admin:
                cleaned_data['department'] = employee.department
            department = cleaned_data.get('department')
            assigned_to = cleaned_data.get('assigned_to')
            task_scope = cleaned_data.get('task_scope', 'individual')
            
            if department and not employee.can_create_tasks_for_department(department):
                raise forms.ValidationError(
                    'У вас нет прав для создания задач в этом отделе'
                )
            
            # Для общих задач assigned_to не требуется
            if task_scope == 'general':
                cleaned_data['assigned_to'] = None
            else:
                # Для индивидуальных задач проверяем assigned_to
                if not assigned_to:
                    raise forms.ValidationError(
                        'Для индивидуальных задач необходимо указать исполнителя'
                    )
                if assigned_to and not employee.is_admin:
                    if not employee.can_assign_tasks_to_employee(assigned_to):
                        raise forms.ValidationError(
                            'У вас нет прав для назначения задач этому сотруднику'
                        )
                    # Проверяем, что сотрудник равного или ниже статуса
                    assignee_level = role_order.get(getattr(assigned_to, 'position', 'employee'), 1)
                    if assignee_level > my_level:
                        raise forms.ValidationError(
                            'Вы не можете назначить задачу сотруднику с более высокой ролью.'
                        )
                if employee.is_admin and assigned_to and department:
                    if assigned_to.department != department:
                        raise forms.ValidationError(
                            'Сотрудник должен принадлежать выбранному отделу.'
                        )
        return cleaned_data


class ShiftLogForm(forms.ModelForm):
    """Форма журнала смены"""
    class Meta:
        model = ShiftLog
        fields = ['start_notes', 'end_notes', 'handover_notes']
        widgets = {
            'start_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'end_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'handover_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class TaskReportForm(forms.ModelForm):
    """Форма отчета по заданию"""
    class Meta:
        model = TaskReport
        fields = ['report_text', 'status']
        widgets = {
            'report_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class AttachmentForm(forms.ModelForm):
    """Форма вложения"""
    class Meta:
        model = Attachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверяем размер файла (50MB)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 50MB')
            
            # Проверяем тип файла
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'application/pdf',
                'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain', 'application/zip', 'application/x-rar-compressed'
            ]
            if file.content_type not in allowed_types:
                raise forms.ValidationError('Неподдерживаемый тип файла')
        
        return file


class ShiftAssignmentForm(forms.ModelForm):
    """Форма назначения на смену"""
    class Meta:
        model = Shift
        fields = []

    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['employees'].initial = self.instance.employees.all()

    def save(self, commit=True):
        shift = super().save(commit=False)
        if commit:
            shift.save()
            shift.employees.set(self.cleaned_data['employees'])
        return shift


class TaskFilterForm(forms.Form):
    """Форма фильтрации заданий"""
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='Отдел',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Все статусы')] + list(Task.STATUS_CHOICES),
        required=False,
        label='Статус',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'Любой приоритет')] + list(Task.PRIORITY_CHOICES),
        required=False,
        label='Приоритет',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    task_type = forms.ChoiceField(
        choices=[('', 'Любой тип')] + list(Task.TASK_TYPE_CHOICES),
        required=False,
        label='Тип задачи',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        label='С даты',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        label='По дату',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'employee'):
            employee = user.employee
            if not employee.is_admin:
                self.fields['department'].queryset = Department.objects.filter(id=employee.department.id)
                self.fields['department'].initial = employee.department
                if self.fields['department'].queryset.count() == 1:
                    self.fields['department'].widget = forms.HiddenInput()


class ShiftFilterForm(forms.Form):
    """Форма фильтрации смен"""
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="Все отделы",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    shift_type = forms.ModelChoiceField(
        queryset=ShiftType.objects.all(),
        required=False,
        empty_label="Все типы смен",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    is_completed = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class TaskStatusUpdateForm(forms.Form):
    """Форма изменения статуса задания"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Новый статус"
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Введите комментарий к изменению статуса...'
        }),
        required=False,
        label="Комментарий"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        comment = cleaned_data.get('comment')
        
        # Если статус меняется на "завершено", комментарий обязателен
        if status == 'completed' and not comment:
            raise forms.ValidationError(
                'При завершении задания обязательно укажите комментарий'
            )
        
        return cleaned_data 


class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': (
                        'Введите или дополните ежедневный отчёт...'
                    )
                }
            )
        }
        labels = {
            'comment': 'Ежедневный отчёт (комментарий)'
        } 


class MaterialWriteOffForm(forms.ModelForm):
    class Meta:
        model = MaterialWriteOff
        fields = ['material_name', 'quantity', 'unit', 'destination', 'department']
        widgets = {
            'material_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'employee'):
            employee = user.employee
            if not employee.is_admin:
                self.fields['department'].widget = forms.HiddenInput()
                self.fields['department'].initial = employee.department
                self.fields['department'].queryset = Department.objects.filter(id=employee.department.id)
            else:
                self.fields['department'].queryset = Department.objects.all() 


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'text']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название заметки'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Введите заметку...'}),
        }
        labels = {
            'title': 'Название',
            'text': 'Текст заметки',
        }
class ProjectTaskForm(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ['project', 'title', 'description', 'due_date', 'status']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'project': 'Проект',
            'title': 'Название задачи',
            'description': 'Описание',
            'due_date': 'Время исполнения',
            'status': 'Статус',
        }
    def __init__(self, *args, **kwargs):
            self.user = kwargs.pop('user', None)
            self.project_instance = kwargs.pop('project_instance', None)
            super().__init__(*args, **kwargs)

            if self.user and hasattr(self.user, 'employee'):
                self.fields['project'].queryset = self.user.employee.projects.all()
            else:
                self.fields['project'].queryset = Project.objects.none()

            if self.project_instance:
                self.fields['project'].widget = forms.HiddenInput()
                self.fields['project'].required = False
                self.fields['project'].initial = self.project_instance.id

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.project_instance:
            instance.project = self.project_instance
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
