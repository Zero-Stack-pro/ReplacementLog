from django.contrib.auth.models import User
from django.test import TestCase

from .models import Department, Employee


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
