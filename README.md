# ZeroStack Replacement Log

Система управления сменами и задачами для производственного отдела.

## Возможности
- Ведение и фильтрация задач по отделам, статусам, приоритетам
- История изменений и комментарии к задачам
- Ежедневные отчёты по отделам
- Уведомления и роли пользователей (админ, руководитель, сотрудник)
- Современный UI/UX на Bootstrap

## Быстрый старт

1. Клонируйте репозиторий:
   ```bash
   git clone <your-repo-url>
   cd ZeroStack_ReplacementLog
   ```
2. Создайте и активируйте виртуальное окружение:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Примените миграции:
   ```bash
   python manage.py migrate
   ```
5. Запустите сервер:
   ```bash
   python manage.py runserver
   ```

## Зависимости
- Python 3.9+
- Django 4.2+
- djangorestframework
- crispy-bootstrap5
- channels
- openpyxl
- pillow
- и др. (см. requirements.txt)

## Структура проекта
- `shift_log/` — основное Django-приложение
- `shift_log_project/` — настройки проекта
- `static/`, `templates/` — статика и шаблоны
- `media/` — вложения пользователей

## Автор
ZeroStack Team 