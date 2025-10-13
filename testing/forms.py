"""
Формы для приложения тестирования функционала.

Содержит формы для создания и редактирования тестовых проектов и функционала.
"""

from django import forms
from django.contrib.auth.models import User

from shift_log.models import Employee

from .models import Feature, FeatureComment, TestProject


class TestProjectForm(forms.ModelForm):
    """Форма для создания и редактирования тестового проекта"""
    
    class Meta:
        model = TestProject
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название проекта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите проект (необязательно)'
            })
        }
        labels = {
            'name': 'Название проекта',
            'description': 'Описание'
        }
        help_texts = {
            'name': 'Краткое название тестового проекта',
            'description': 'Подробное описание проекта (необязательно)'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        """Валидация названия проекта"""
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError('Название проекта обязательно')
        
        if len(name.strip()) < 3:
            raise forms.ValidationError('Название должно содержать минимум 3 символа')
        
        # Проверяем уникальность в рамках создателя
        if self.user and hasattr(self.user, 'employee'):
            employee = self.user.employee
            queryset = TestProject.objects.filter(
                name=name.strip(),
                created_by=employee
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError('Проект с таким названием уже существует')
        
        return name.strip()


class FeatureForm(forms.ModelForm):
    """Форма для создания и редактирования функционала"""
    
    class Meta:
        model = Feature
        fields = ['test_project', 'title', 'description', 'priority']
        widgets = {
            'test_project': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название функционала'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Подробно опишите функционал'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'test_project': 'Тестовый проект',
            'title': 'Название функционала',
            'description': 'Описание',
            'priority': 'Приоритет'
        }
        help_texts = {
            'test_project': 'Выберите проект для функционала',
            'title': 'Краткое название функционала',
            'description': 'Подробное описание функционала',
            'priority': 'Приоритет выполнения'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Фильтруем проекты в зависимости от прав пользователя
        if self.user and hasattr(self.user, 'employee'):
            employee = self.user.employee
            if employee.position == 'admin':
                # Администраторы видят все проекты
                self.fields['test_project'].queryset = TestProject.objects.filter(is_active=True)
            elif employee.role in ['programmer', 'tester']:
                # Программисты и тестировщики видят все активные проекты
                self.fields['test_project'].queryset = TestProject.objects.filter(is_active=True)
            else:
                # Остальные видят только свои проекты
                self.fields['test_project'].queryset = TestProject.objects.filter(
                    created_by=employee,
                    is_active=True
                )

    def clean_title(self):
        """Валидация названия функционала"""
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError('Название функционала обязательно')
        
        if len(title.strip()) < 5:
            raise forms.ValidationError('Название должно содержать минимум 5 символов')
        
        return title.strip()

    def clean_description(self):
        """Валидация описания функционала"""
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError('Описание функционала обязательно')
        
        if len(description.strip()) < 20:
            raise forms.ValidationError('Описание должно содержать минимум 20 символов')
        
        return description.strip()


class FeatureCommentForm(forms.ModelForm):
    """Форма для добавления замечания к функционалу"""
    
    class Meta:
        model = FeatureComment
        fields = ['comment', 'comment_type']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Введите текст замечания'
            }),
            'comment_type': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'comment': 'Текст замечания',
            'comment_type': 'Тип замечания'
        }
        help_texts = {
            'comment': 'Подробно опишите замечание или предложение',
            'comment_type': 'Выберите тип комментария'
        }

    def clean_comment(self):
        """Валидация текста замечания"""
        comment = self.cleaned_data.get('comment')
        if not comment:
            raise forms.ValidationError('Текст замечания обязателен')
        
        if len(comment.strip()) < 2:
            raise forms.ValidationError('Замечание должно содержать минимум 2 символа')
        
        return comment.strip()


class FeatureCommentReworkForm(forms.Form):
    """Форма для возврата замечания на доработку"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Укажите причину возврата замечания на доработку'
        }),
        label='Причина возврата на доработку',
        help_text='Обязательно укажите причину возврата замечания на доработку'
    )

    def clean_reason(self):
        """Валидация причины возврата"""
        reason = self.cleaned_data.get('reason')
        if not reason:
            raise forms.ValidationError('Причина возврата на доработку обязательна')
        
        if len(reason.strip()) < 5:
            raise forms.ValidationError('Причина должна содержать минимум 5 символов')
        
        return reason.strip()


class FeatureStatusUpdateForm(forms.Form):
    """Форма для изменения статуса функционала"""
    
    status = forms.ChoiceField(
        choices=Feature.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Новый статус',
        help_text='Выберите новый статус для функционала'
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Комментарий к изменению статуса (необязательно)'
        }),
        label='Комментарий',
        help_text='Дополнительный комментарий к изменению статуса'
    )

    def __init__(self, *args, **kwargs):
        self.feature = kwargs.pop('feature', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор статусов в зависимости от прав пользователя
        if self.feature and self.user and hasattr(self.user, 'employee'):
            employee = self.user.employee
            from .services.feature_service import FeatureService
            
            available_statuses = FeatureService.get_available_status_transitions(
                self.feature, employee
            )
            
            # Фильтруем choices
            current_choices = dict(Feature.STATUS_CHOICES)
            filtered_choices = [
                (status, current_choices[status]) 
                for status in available_statuses
            ]
            
            self.fields['status'].choices = filtered_choices


class FeatureFilterForm(forms.Form):
    """Форма для фильтрации списка функционала"""
    
    STATUS_CHOICES = [('', 'Все статусы')] + list(Feature.STATUS_CHOICES)
    PRIORITY_CHOICES = [('', 'Все приоритеты')] + list(Feature.PRIORITY_CHOICES)
    
    test_project = forms.ModelChoiceField(
        queryset=TestProject.objects.filter(is_active=True),
        required=False,
        empty_label="Все проекты",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Проект'
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Статус'
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Приоритет'
    )
    created_by = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        empty_label="Все создатели",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Создатель'
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию или описанию...'
        }),
        label='Поиск'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Фильтруем проекты в зависимости от прав пользователя
        if self.user and hasattr(self.user, 'employee'):
            employee = self.user.employee
            if employee.position == 'admin':
                # Администраторы видят все проекты
                pass
            else:
                # Остальные видят только свои проекты
                self.fields['test_project'].queryset = TestProject.objects.filter(
                    created_by=employee,
                    is_active=True
                )


class TestProjectFilterForm(forms.Form):
    """Форма для фильтрации списка тестовых проектов"""
    
    created_by = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        empty_label="Все создатели",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Создатель'
    )
    is_active = forms.ChoiceField(
        choices=[('', 'Все'), ('true', 'Активные'), ('false', 'Неактивные')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Статус'
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию или описанию...'
        }),
        label='Поиск'
    )
