from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Department, Employee, Task, TaskProject


class EmployeeRoleTestCase(TestCase):
    """Тесты для функционала ролей сотрудников"""

    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем отдел
        self.department = Department.objects.create(
            name="Тестовый отдел",
            description="Отдел для тестирования"
        )

        # Создаем пользователей
        self.user1 = User.objects.create_user(
            username='programmer',
            email='programmer@test.com',
            first_name='Иван',
            last_name='Программист'
        )

        self.user2 = User.objects.create_user(
            username='tester',
            email='tester@test.com',
            first_name='Петр',
            last_name='Тестировщик'
        )

        self.user3 = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            first_name='Сидор',
            last_name='Сотрудник'
        )

        # Создаем сотрудников с разными ролями
        self.programmer = Employee.objects.create(
            user=self.user1,
            department=self.department,
            position='employee',
            role='programmer'
        )

        self.tester = Employee.objects.create(
            user=self.user2,
            department=self.department,
            position='employee',
            role='tester'
        )

        self.employee = Employee.objects.create(
            user=self.user3,
            department=self.department,
            position='employee',
            role=None
        )
    
    def test_role_display_name(self):
        """Тест отображения названий ролей"""
        self.assertEqual(
            self.programmer.get_role_display_name(), 'Программист'
        )
        self.assertEqual(
            self.tester.get_role_display_name(), 'Тестировщик'
        )
        self.assertIsNone(self.employee.get_role_display_name())

    def test_role_properties(self):
        """Тест свойств ролей"""
        self.assertTrue(self.programmer.is_programmer)
        self.assertFalse(self.programmer.is_tester)

        self.assertTrue(self.tester.is_tester)
        self.assertFalse(self.tester.is_programmer)

        self.assertFalse(self.employee.is_programmer)
        self.assertFalse(self.employee.is_tester)

    def test_full_role_display(self):
        """Тест полного отображения должности и роли"""
        self.assertEqual(
            self.programmer.get_full_role_display(),
            'Сотрудник (Программист)'
        )
        self.assertEqual(
            self.tester.get_full_role_display(),
            'Сотрудник (Тестировщик)'
        )
        self.assertEqual(
            self.employee.get_full_role_display(),
            'Сотрудник'
        )

    def test_employee_str_with_role(self):
        """Тест строкового представления сотрудника с ролью"""
        expected_str = (
            f"{self.programmer.user.get_full_name()} (Программист) - "
            f"{self.department.name}"
        )
        self.assertEqual(str(self.programmer), expected_str)

        expected_str = (
            f"{self.tester.user.get_full_name()} (Тестировщик) - "
            f"{self.department.name}"
        )
        self.assertEqual(str(self.tester), expected_str)

        expected_str = (
            f"{self.employee.user.get_full_name()} - "
            f"{self.department.name}"
        )
        self.assertEqual(str(self.employee), expected_str)

    def test_role_choices(self):
        """Тест выбора ролей"""
        role_choices = Employee.ROLE_CHOICES
        self.assertEqual(len(role_choices), 2)
        self.assertIn(('programmer', 'Программист'), role_choices)
        self.assertIn(('tester', 'Тестировщик'), role_choices)

    def test_role_field_optional(self):
        """Тест что поле роли необязательное"""
        # Создаем сотрудника без роли
        user4 = User.objects.create_user(
            username='no_role',
            email='norole@test.com',
            first_name='Без',
            last_name='Роли'
        )

        employee_no_role = Employee.objects.create(
            user=user4,
            department=self.department,
            position='employee'
            # role не указан
        )

        self.assertIsNone(employee_no_role.role)
        self.assertFalse(employee_no_role.is_programmer)
        self.assertFalse(employee_no_role.is_tester)
        self.assertEqual(
            employee_no_role.get_full_role_display(), 'Сотрудник'
        )


class TaskCreationFlowTestCase(TestCase):
    """Тесты создания задач с датой и проектом."""

    def setUp(self):
        """Создание общих сущностей для тестов."""
        self.department = Department.objects.create(
            name='Основной отдел',
            description='Описание'
        )
        self.admin_user = User.objects.create_user(
            username='admin_user',
            password='testpass123',
            email='admin@example.com'
        )
        self.admin_employee = Employee.objects.create(
            user=self.admin_user,
            department=self.department,
            position='admin'
        )
        self.assignee_user = User.objects.create_user(
            username='worker',
            password='testpass123',
            email='worker@example.com'
        )
        self.assignee_employee = Employee.objects.create(
            user=self.assignee_user,
            department=self.department,
            position='employee'
        )

    def _base_payload(self, **overrides):
        payload = {
            'title': 'Новая задача',
            'description': 'Описание задачи',
            'comment': '',
            'department': str(self.department.id),
            'assigned_to': str(self.assignee_employee.id),
            'priority': '2',
            'task_type': 'routine',
            'task_scope': 'individual',
            'due_date': '2025-07-10T14:30',
            'project': '',
            'project_name': '',
        }
        payload.update(overrides)
        return payload

    def test_task_create_accepts_datetime_local_format(self):
        """Проверяет, что формат datetime-local проходит валидацию."""
        self.client.login(username='admin_user', password='testpass123')
        response = self.client.post(
            reverse('shift_log:task_create'),
            data=self._base_payload(),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.first()
        self.assertIsNotNone(task)
        self.assertEqual(
            timezone.localtime(task.due_date).strftime('%Y-%m-%dT%H:%M'),
            '2025-07-10T14:30'
        )

    def test_task_create_with_new_project_option(self):
        """Проверяет создание нового проекта при выборе опции."""
        self.client.login(username='admin_user', password='testpass123')
        response = self.client.post(
            reverse('shift_log:task_create'),
            data=self._base_payload(
                project='__new__',
                project_name='Проект А'
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TaskProject.objects.count(), 1)
        project = TaskProject.objects.first()
        self.assertIsNotNone(project)
        self.assertEqual(project.name, 'Проект А')
        task = Task.objects.first()
        self.assertIsNotNone(task)
        self.assertEqual(task.project, project)
