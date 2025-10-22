"""
Представления для приложения тестирования функционала.

Использует Class-Based Views согласно Django Best Practices.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (CreateView, DetailView, ListView, UpdateView,
                                  View)

from .forms import (FeatureCommentCompleteForm, FeatureCommentForm,
                    FeatureCommentReworkForm, FeatureFilterForm, FeatureForm,
                    FeatureStatusUpdateForm, TestProjectFilterForm,
                    TestProjectForm)
from .models import Feature, FeatureComment, TestProject
from .services.feature_service import FeatureService, TestProjectService


class TestProjectListView(LoginRequiredMixin, ListView):
    """Список тестовых проектов"""
    
    model = TestProject
    template_name = 'testing/testproject_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        """Возвращает queryset проектов с учетом прав доступа"""
        queryset = TestProject.objects.select_related('created_by', 'created_by__user')
        
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            
            if employee.position == 'admin':
                # Администраторы видят все проекты
                pass
            elif employee.role in ['programmer', 'tester']:
                # Программисты и тестировщики видят все активные проекты
                queryset = queryset.filter(is_active=True)
            else:
                # Остальные видят только свои проекты
                queryset = queryset.filter(created_by=employee)
        
        # Применяем фильтры
        form = TestProjectFilterForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            if form.cleaned_data.get('created_by'):
                queryset = queryset.filter(created_by=form.cleaned_data['created_by'])
            
            if form.cleaned_data.get('is_active'):
                is_active = form.cleaned_data['is_active'] == 'true'
                queryset = queryset.filter(is_active=is_active)
            
            if form.cleaned_data.get('search'):
                search_term = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(description__icontains=search_term)
                )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        context['filter_form'] = TestProjectFilterForm(self.request.GET, user=self.request.user)
        
        if hasattr(self.request.user, 'employee'):
            context['employee'] = self.request.user.employee
            context['can_create_project'] = TestProjectService.can_create_project(
                self.request.user.employee
            )
        
        return context


class TestProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание нового тестового проекта"""
    
    model = TestProject
    form_class = TestProjectForm
    template_name = 'testing/testproject_form.html'
    success_url = reverse_lazy('testing:testproject_list')

    def test_func(self):
        """Проверяет права на создание проекта"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        return TestProjectService.can_create_project(self.request.user.employee)

    def get_form_kwargs(self):
        """Передает пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Обрабатывает валидную форму"""
        try:
            project = TestProjectService.create_project(
                employee=self.request.user.employee,
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description']
            )
            messages.success(self.request, f'Проект "{project.name}" успешно создан')
            return redirect('testing:testproject_detail', pk=project.pk)
        except Exception as e:
            messages.error(self.request, f'Ошибка при создании проекта: {str(e)}')
            return self.form_invalid(form)


class TestProjectDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о тестовом проекте"""
    
    model = TestProject
    template_name = 'testing/testproject_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        """Возвращает queryset с учетом прав доступа"""
        queryset = TestProject.objects.select_related('created_by', 'created_by__user')
        
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            
            if employee.position == 'admin':
                # Администраторы видят все проекты
                pass
            elif employee.role in ['programmer', 'tester']:
                # Программисты и тестировщики видят все активные проекты
                queryset = queryset.filter(is_active=True)
            else:
                # Остальные видят только свои проекты
                queryset = queryset.filter(created_by=employee)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Получаем функционал проекта
        features = project.features.select_related('created_by', 'created_by__user').order_by(
            '-priority', '-created_at'
        )
        
        # Статистика по статусам
        status_stats = {}
        for status_code, status_name in Feature.STATUS_CHOICES:
            count = features.filter(status=status_code).count()
            if count > 0:
                status_stats[status_code] = {
                    'name': status_name,
                    'count': count
                }
        
        context.update({
            'features': features,
            'status_stats': status_stats,
            'employee': self.request.user.employee if hasattr(self.request.user, 'employee') else None,
            'can_create_feature': FeatureService.can_create_feature(
                self.request.user.employee
            ) if hasattr(self.request.user, 'employee') else False
        })
        
        return context


class TestProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование тестового проекта"""
    
    model = TestProject
    form_class = TestProjectForm
    template_name = 'testing/testproject_form.html'
    success_url = reverse_lazy('testing:testproject_list')

    def test_func(self):
        """Проверяет права на редактирование проекта"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        employee = self.request.user.employee
        project = self.get_object()
        
        return (
            employee.position == 'admin' or 
            project.created_by == employee
        )

    def get_queryset(self):
        """Возвращает queryset с учетом прав доступа"""
        queryset = TestProject.objects.all()
        
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            
            if employee.position == 'admin':
                # Администраторы видят все проекты
                pass
            else:
                # Остальные видят только свои проекты
                queryset = queryset.filter(created_by=employee)
        
        return queryset

    def get_form_kwargs(self):
        """Передает пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Обрабатывает валидную форму"""
        messages.success(self.request, f'Проект "{form.instance.name}" успешно обновлен')
        return super().form_valid(form)


class FeatureListView(LoginRequiredMixin, ListView):
    """Список функционала для тестирования с группировкой по проектам"""
    
    model = Feature
    template_name = 'testing/feature_list.html'
    context_object_name = 'features_by_project'

    def get_queryset(self):
        """Возвращает queryset функционала с учетом прав доступа"""
        queryset = Feature.objects.select_related(
            'test_project', 'created_by', 'created_by__user'
        ).prefetch_related('comments')
        
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            
            if employee.position == 'admin':
                # Администраторы видят весь функционал
                pass
            elif employee.role == 'tester':
                # Тестировщики видят весь функционал
                pass
            else:
                # Программисты видят только свой функционал
                queryset = queryset.filter(created_by=employee)
        
        # Применяем фильтры
        form = FeatureFilterForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            if form.cleaned_data.get('test_project'):
                queryset = queryset.filter(test_project=form.cleaned_data['test_project'])
            
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            
            if form.cleaned_data.get('priority'):
                queryset = queryset.filter(priority=form.cleaned_data['priority'])
            
            if form.cleaned_data.get('created_by'):
                queryset = queryset.filter(created_by=form.cleaned_data['created_by'])
            
            if form.cleaned_data.get('search'):
                search_term = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(description__icontains=search_term)
                )
        
        return queryset.order_by('test_project__name', '-priority', '-created_at')

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        context['filter_form'] = FeatureFilterForm(self.request.GET, user=self.request.user)
        
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            context['employee'] = employee
            context['can_create_feature'] = FeatureService.can_create_feature(employee)
        
        # Группируем фичи по проектам
        features = self.get_queryset()
        features_by_project = {}
        
        for feature in features:
            project = feature.test_project
            if project not in features_by_project:
                features_by_project[project] = []
            
            # Добавляем информацию о правах редактирования
            if hasattr(self.request.user, 'employee'):
                feature.can_be_edited_by = feature.can_be_edited_by(self.request.user.employee)
            
            features_by_project[project].append(feature)
        
        context['features_by_project'] = features_by_project
        
        return context


class FeatureCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание нового функционала"""
    
    model = Feature
    form_class = FeatureForm
    template_name = 'testing/feature_form.html'
    success_url = reverse_lazy('testing:feature_list')

    def test_func(self):
        """Проверяет права на создание функционала"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        return FeatureService.can_create_feature(self.request.user.employee)

    def get_form_kwargs(self):
        """Передает пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Обрабатывает валидную форму"""
        try:
            feature = FeatureService.create_feature(
                employee=self.request.user.employee,
                test_project=form.cleaned_data['test_project'],
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority']
            )
            messages.success(self.request, f'Функционал "{feature.title}" успешно создан')
            return redirect('testing:feature_detail', pk=feature.pk)
        except Exception as e:
            messages.error(self.request, f'Ошибка при создании функционала: {str(e)}')
            return self.form_invalid(form)


class FeatureDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о функционале"""
    
    model = Feature
    template_name = 'testing/feature_detail.html'
    context_object_name = 'feature'

    def get_queryset(self):
        """Возвращает queryset с учетом прав доступа"""
        queryset = Feature.objects.select_related(
            'test_project', 'created_by', 'created_by__user'
        ).prefetch_related('comments', 'comments__author', 'attachments')
        
        if hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            
            if employee.position == 'admin':
                # Администраторы видят весь функционал
                pass
            elif employee.role == 'tester':
                # Тестировщики видят весь функционал
                pass
            else:
                # Программисты видят только свой функционал
                queryset = queryset.filter(created_by=employee)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        feature = self.get_object()
        
        # Получаем замечания сгруппированные по статусу
        all_comments = feature.comments.select_related('author', 'author__user').order_by('-created_at')
        
        # Группируем замечания по статусу
        open_comments = all_comments.filter(status__in=['open', 'in_progress', 'rework'])
        resolved_comments = all_comments.filter(status='resolved')
        completed_comments = all_comments.filter(status='completed')
        
        # Получаем историю замечаний
        comment_history = []
        for comment in all_comments:
            history = comment.history.select_related('changed_by', 'changed_by__user').order_by('-changed_at')
            comment_history.extend(history)
        
        # Сортируем всю историю по дате
        comment_history.sort(key=lambda x: x.changed_at, reverse=True)
        
        # Получаем вложения
        attachments = feature.attachments.select_related('uploaded_by', 'uploaded_by__user').order_by('-uploaded_at')
        
        # Формы
        comment_form = FeatureCommentForm()
        
        # Проверяем права
        employee = self.request.user.employee if hasattr(self.request.user, 'employee') else None
        can_edit = feature.can_be_edited_by(employee) if employee else False
        
        context.update({
            'open_comments': open_comments,
            'resolved_comments': resolved_comments,
            'completed_comments': completed_comments,
            'comment_history': comment_history,
            'attachments': attachments,
            'comment_form': comment_form,
            'employee': employee,
            'can_edit': can_edit
        })
        
        return context


class FeatureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование функционала"""
    
    model = Feature
    form_class = FeatureForm
    template_name = 'testing/feature_form.html'
    
    def test_func(self):
        """Проверяет права на редактирование функционала"""
        if not hasattr(self.request.user, 'employee'):
            return False
        
        feature = self.get_object()
        employee = self.request.user.employee
        
        return feature.can_be_edited_by(employee)
    
    def get_form_kwargs(self):
        """Передает пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Обрабатывает валидную форму"""
        try:
            feature = self.get_object()
            employee = self.request.user.employee
            
            FeatureService.update_feature(
                feature=feature,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority'],
                employee=employee
            )
            messages.success(self.request, 'Функционал успешно обновлен')
            return redirect('testing:feature_detail', pk=feature.pk)
        except Exception as e:
            messages.error(self.request, f'Ошибка при обновлении функционала: {str(e)}')
            return self.form_invalid(form)


class FeatureUpdateStatusView(LoginRequiredMixin, View):
    """Изменение статуса функционала"""
    
    def post(self, request, pk):
        """Обрабатывает POST-запрос для изменения статуса"""
        feature = get_object_or_404(Feature, pk=pk)
        
        if not hasattr(request.user, 'employee'):
            messages.error(request, 'Профиль сотрудника не найден')
            return redirect('testing:feature_detail', pk=pk)
        
        employee = request.user.employee
        
        form = FeatureStatusUpdateForm(request.POST, feature=feature, user=request.user)
        if form.is_valid():
            try:
                FeatureService.update_feature_status(
                    feature=feature,
                    new_status=form.cleaned_data['status'],
                    employee=employee,
                    comment=form.cleaned_data.get('comment', '')
                )
                messages.success(request, 'Статус функционала успешно обновлен')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении статуса: {str(e)}')
        else:
            messages.error(request, 'Ошибка в форме')
        
        return redirect('testing:feature_detail', pk=pk)


class FeatureAddCommentView(LoginRequiredMixin, View):
    """Добавление замечания к функционалу"""
    
    def post(self, request, pk):
        """Обрабатывает POST-запрос для добавления замечания"""
        print(f"DEBUG: POST-запрос для добавления замечания к функционалу {pk}")
        print(f"DEBUG: Данные POST: {request.POST}")
        
        feature = get_object_or_404(Feature, pk=pk)
        print(f"DEBUG: Функционал найден: {feature.title}")
        
        if not hasattr(request.user, 'employee'):
            print("DEBUG: Профиль сотрудника не найден")
            messages.error(request, 'Профиль сотрудника не найден')
            return redirect('testing:feature_detail', pk=pk)
        
        employee = request.user.employee
        print(f"DEBUG: Сотрудник: {employee.get_full_name()}, роль: {employee.role}, позиция: {employee.position}")
        
        # Проверяем права на добавление замечаний
        if not (employee.position == 'admin' or employee.role == 'tester'):
            print("DEBUG: Недостаточно прав для добавления замечаний")
            messages.error(request, 'У вас нет прав для добавления замечаний')
            return redirect('testing:feature_detail', pk=pk)
        
        form = FeatureCommentForm(request.POST)
        print(f"DEBUG: Форма создана, валидна: {form.is_valid()}")
        
        if form.is_valid():
            print(f"DEBUG: Форма валидна, данные: {form.cleaned_data}")
            try:
                comment = FeatureService.add_comment(
                    feature=feature,
                    employee=employee,
                    comment_text=form.cleaned_data['comment'],
                    comment_type=form.cleaned_data['comment_type']
                )
                print(f"DEBUG: Замечание добавлено успешно: {comment.id}")
                messages.success(request, 'Замечание успешно добавлено')
            except Exception as e:
                print(f"DEBUG: Ошибка при добавлении замечания: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Ошибка при добавлении замечания: {str(e)}')
        else:
            print(f"DEBUG: Форма невалидна, ошибки: {form.errors}")
            messages.error(request, f'Ошибка в форме: {form.errors}')
        
        return redirect('testing:feature_detail', pk=pk)


class FeatureReturnToReworkView(LoginRequiredMixin, View):
    """Возврат функционала на доработку"""
    
    def post(self, request, pk):
        """Обрабатывает POST-запрос для возврата на доработку"""
        feature = get_object_or_404(Feature, pk=pk)
        
        if not hasattr(request.user, 'employee'):
            messages.error(request, 'Профиль сотрудника не найден')
            return redirect('testing:feature_detail', pk=pk)
        
        employee = request.user.employee
        
        # Получаем комментарий из формы
        comment = request.POST.get('comment', '')
        
        try:
            FeatureService.return_to_rework(
                feature=feature,
                employee=employee,
                comment=comment
            )
            messages.success(request, 'Функционал возвращен на доработку')
        except PermissionError as e:
            messages.error(request, str(e))
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при возврате на доработку: {str(e)}')
        
        return redirect('testing:feature_detail', pk=pk)


@csrf_exempt
def mark_completed_api(request, pk):
    """API для отметки функционала как выполненного"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        feature = get_object_or_404(Feature, pk=pk)
        
        if not hasattr(request.user, 'employee'):
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
        
        employee = request.user.employee
        
        FeatureService.mark_as_completed(feature, employee)
        
        return JsonResponse({
            'success': True,
            'message': 'Функционал отмечен как выполненный',
            'new_status': feature.status
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class FeatureResolveCommentView(LoginRequiredMixin, View):
    """Отметка замечания как решенного и запрос повторной проверки"""
    
    def post(self, request, pk, comment_id):
        """Обрабатывает POST-запрос для отметки замечания как решенного"""
        feature = get_object_or_404(Feature, pk=pk)
        comment = get_object_or_404(FeatureComment, pk=comment_id, feature=feature)
        
        if not hasattr(request.user, 'employee'):
            messages.error(request, 'Профиль сотрудника не найден')
            return redirect('testing:feature_detail', pk=pk)
        
        employee = request.user.employee
        
        try:
            comment.mark_as_resolved(employee)
            
            # Создаем запись в истории
            from .models import FeatureCommentHistory
            FeatureCommentHistory.objects.create(
                comment=comment,
                action='resolved',
                changed_by=employee,
                reason='Замечание отмечено как решенное программистом'
            )
            
            messages.success(request, 'Замечание отмечено как решенное. Требуется повторная проверка.')
        except PermissionError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при отметке замечания: {str(e)}')
        
        return redirect('testing:feature_detail', pk=pk)


class FeatureCommentReturnToReworkView(LoginRequiredMixin, View):
    """Возврат замечания на доработку"""
    
    def post(self, request, pk, comment_id):
        """Обрабатывает POST-запрос для возврата замечания на доработку"""
        feature = get_object_or_404(Feature, pk=pk)
        comment = get_object_or_404(FeatureComment, pk=comment_id, feature=feature)
        
        if not hasattr(request.user, 'employee'):
            messages.error(request, 'Профиль сотрудника не найден')
            return redirect('testing:feature_detail', pk=pk)
        
        employee = request.user.employee
        
        form = FeatureCommentReworkForm(request.POST)
        if form.is_valid():
            try:
                FeatureService.return_comment_to_rework(
                    feature=feature,
                    comment=comment,
                    employee=employee,
                    reason=form.cleaned_data['reason']
                )
                
                messages.success(request, 'Замечание возвращено на доработку')
            except PermissionError as e:
                messages.error(request, str(e))
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Ошибка при возврате замечания на доработку: {str(e)}')
        else:
            # Показываем ошибки валидации
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
        
        return redirect('testing:feature_detail', pk=pk)


class FeatureCommentCompleteView(LoginRequiredMixin, View):
    """Завершение замечания тестировщиком или администратором"""
    
    def post(self, request, pk, comment_id):
        """Обрабатывает POST-запрос для завершения замечания"""
        feature = get_object_or_404(Feature, pk=pk)
        comment = get_object_or_404(FeatureComment, pk=comment_id, feature=feature)
        
        if not hasattr(request.user, 'employee'):
            messages.error(request, 'Профиль сотрудника не найден')
            return redirect('testing:feature_detail', pk=pk)
        
        employee = request.user.employee
        
        form = FeatureCommentCompleteForm(request.POST)
        if form.is_valid():
            try:
                FeatureService.complete_comment(
                    feature=feature,
                    comment=comment,
                    employee=employee,
                    completion_comment=form.cleaned_data.get('comment', '')
                )
                
                messages.success(request, 'Замечание успешно завершено')
            except PermissionError as e:
                messages.error(request, str(e))
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Ошибка при завершении замечания: {str(e)}')
        else:
            # Показываем ошибки валидации
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
        
        return redirect('testing:feature_detail', pk=pk)