from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from shift_log.models import Department, Employee, ShiftType
from shift_log.utils import generate_shift_schedule, validate_shift_pattern


class Command(BaseCommand):
    help = 'Генерирует смены для отделов на основе их типов смен'

    def add_arguments(self, parser):
        parser.add_argument(
            '--department',
            type=str,
            help='Название отдела (если не указано, генерирует для всех)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Начальная дата (YYYY-MM-DD)',
            default=(date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='Конечная дата (YYYY-MM-DD)',
            default=(date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        )
        parser.add_argument(
            '--employees',
            type=str,
            help='ID сотрудников через запятую для назначения на смены'
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Только валидировать типы смен без создания'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Создавать смены даже если они уже существуют'
        )

    def handle(self, *args, **options):
        try:
            start_date = date.fromisoformat(options['start_date'])
            end_date = date.fromisoformat(options['end_date'])
        except ValueError as e:
            raise CommandError(f'Неверный формат даты: {e}')

        if start_date >= end_date:
            raise CommandError('Начальная дата должна быть меньше конечной')

        # Получаем отделы
        if options['department']:
            try:
                departments = [Department.objects.get(name=options['department'])]
            except Department.DoesNotExist:
                raise CommandError(f'Отдел "{options["department"]}" не найден')
        else:
            departments = Department.objects.all()

        if not departments:
            raise CommandError('Не найдено ни одного отдела')

        # Получаем сотрудников
        employees = None
        if options['employees']:
            try:
                employee_ids = [int(id.strip()) for id in options['employees'].split(',')]
                employees = list(Employee.objects.filter(id__in=employee_ids))
                if len(employees) != len(employee_ids):
                    found_ids = [emp.id for emp in employees]
                    missing_ids = set(employee_ids) - set(found_ids)
                    self.stdout.write(
                        self.style.WARNING(
                            f'Сотрудники с ID {missing_ids} не найдены'
                        )
                    )
            except ValueError:
                raise CommandError('Неверный формат ID сотрудников')

        # Валидируем типы смен
        self.stdout.write('Валидация типов смен...')
        validation_errors = []
        
        for department in departments:
            shift_types = ShiftType.objects.filter(department=department, is_active=True)
            
            if not shift_types:
                self.stdout.write(
                    self.style.WARNING(
                        f'Для отдела "{department.name}" не найдено активных типов смен'
                    )
                )
                continue
            
            for shift_type in shift_types:
                errors = validate_shift_pattern(shift_type)
                if errors:
                    validation_errors.append({
                        'department': department.name,
                        'shift_type': shift_type.name,
                        'errors': errors
                    })
                    self.stdout.write(
                        self.style.ERROR(
                            f'Ошибки в типе смены "{shift_type.name}" отдела "{department.name}":'
                        )
                    )
                    for error in errors:
                        self.stdout.write(f'  - {error}')
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Тип смены "{shift_type.name}" отдела "{department.name}" валиден'
                        )
                    )

        if validation_errors:
            self.stdout.write(
                self.style.ERROR(
                    'Обнаружены ошибки валидации. Исправьте их перед генерацией смен.'
                )
            )
            return

        if options['validate_only']:
            self.stdout.write(
                self.style.SUCCESS('Валидация завершена успешно')
            )
            return

        # Генерируем смены
        self.stdout.write('Генерация смен...')
        
        total_created = 0
        total_errors = 0
        
        for department in departments:
            self.stdout.write(f'Обработка отдела: {department.name}')
            
            try:
                results = generate_shift_schedule(
                    department=department,
                    start_date=start_date,
                    end_date=end_date,
                    employees=employees
                )
                
                if results['total_shifts_created'] > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Создано {results["total_shifts_created"]} смен'
                        )
                    )
                    
                    for shift_type_name, count in results['shifts_by_type'].items():
                        self.stdout.write(f'  - {shift_type_name}: {count} смен')
                    
                    total_created += results['total_shifts_created']
                else:
                    self.stdout.write(
                        self.style.WARNING('Смены не созданы (возможно, уже существуют)')
                    )
                
                if results['errors']:
                    for error in results['errors']:
                        self.stdout.write(self.style.ERROR(f'  Ошибка: {error}'))
                        total_errors += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при обработке отдела {department.name}: {e}')
                )
                total_errors += 1

        # Итоговая статистика
        self.stdout.write('\n' + '='*50)
        self.stdout.write('ИТОГИ ГЕНЕРАЦИИ:')
        self.stdout.write(f'Период: {start_date} - {end_date}')
        self.stdout.write(f'Отделов обработано: {len(departments)}')
        self.stdout.write(f'Всего смен создано: {total_created}')
        self.stdout.write(f'Ошибок: {total_errors}')
        
        if total_created > 0:
            self.stdout.write(
                self.style.SUCCESS('Генерация смен завершена успешно!')
            )
        elif total_errors == 0:
            self.stdout.write(
                self.style.WARNING('Смены не созданы (возможно, уже существуют)')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Генерация завершена с ошибками')
            ) 