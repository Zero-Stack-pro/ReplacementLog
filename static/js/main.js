// Основной JavaScript файл для системы сменного журнала

console.log('main.js загружен, jQuery доступен:', typeof $ !== 'undefined');
console.log('Текущий путь:', window.location.pathname);

$(document).ready(function () {
    console.log('DOM загружен, инициализация компонентов...');
    // Инициализация всех компонентов
    initThemeToggle();
    initNotifications();
    initTaskStatusUpdates();
    initFileUploads();
    initFilters();
    initTooltips();
    initAutoRefresh();
    console.log('Все компоненты инициализированы');
});

// Уведомления
function initNotifications() {
    // Обновление счетчика уведомлений
    function updateNotificationCount() {
        console.log('Обновляем счетчик уведомлений...');
        $.ajax({
            url: '/api/notifications/count/?t=' + new Date().getTime(),
            method: 'GET',
            cache: false,
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            success: function (response) {
                console.log('Получен ответ для счетчика:', response);
                var countElement = $('#notification-count');
                console.log('Элемент счетчика найден:', countElement.length > 0);

                if (response.count > 0) {
                    countElement.text(response.count).show();
                    console.log('Счетчик обновлен на:', response.count);
                } else {
                    countElement.hide();
                    console.log('Счетчик скрыт (нет уведомлений)');
                }
            },
            error: function (xhr, status, error) {
                console.log('Ошибка при обновлении счетчика:', xhr, status, error);
            }
        });
    }

    // Загрузка уведомлений в выпадающее меню
    function loadNotifications() {
        $.ajax({
            url: '/api/notifications/recent/?t=' + new Date().getTime(),
            method: 'GET',
            cache: false,
            success: function (response) {
                var menu = $('#notifications-menu');
                menu.find('.dropdown-item:not(:last)').remove();

                if (response.notifications.length > 0) {
                    response.notifications.forEach(function (notification) {
                        var item = $('<li><a class="dropdown-item notification-item" href="#"></a></li>');
                        var statusClass = notification.is_read ? 'text-muted' : 'fw-bold';
                        item.find('a').html(
                            '<div class="' + statusClass + '">' +
                            '<strong>' + notification.title + '</strong><br>' +
                            '<small class="text-muted">' + notification.message + '</small>' +
                            '</div>'
                        );
                        menu.find('.dropdown-divider').before(item);
                    });
                } else {
                    var item = $('<li><span class="dropdown-item text-muted">Нет новых уведомлений</span></li>');
                    menu.find('.dropdown-divider').before(item);
                }
            }
        });
    }

    // Отметить уведомление как прочитанное
    $(document).on('click', '.mark-read', function () {
        var notificationId = $(this).data('notification-id');
        var button = $(this);

        console.log('Кнопка нажата, notificationId:', notificationId);
        console.log('CSRF токен:', getCSRFToken());

        $.ajax({
            url: '/notifications/' + notificationId + '/read/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            success: function (response) {
                console.log('Успешный ответ:', response);
                if (response.success) {
                    // Находим родительский элемент уведомления
                    var notificationElement = button.closest('.notification-item');
                    console.log('Найденный элемент уведомления:', notificationElement);
                    if (notificationElement.length > 0) {
                        notificationElement.fadeOut(300, function () {
                            $(this).remove();

                            // Проверяем, остались ли еще уведомления
                            var remainingNotifications = $('.notification-item').length;
                            console.log('Оставшиеся уведомления:', remainingNotifications);
                            if (remainingNotifications === 0) {
                                // Если уведомлений больше нет, показываем сообщение только в карточке уведомлений
                                var notificationsCard = $('#notifications-card');
                                if (notificationsCard.length > 0) {
                                    var cardBody = notificationsCard.find('.card-body');
                                    if (cardBody.length > 0) {
                                        cardBody.html('<div class="text-center py-4"><i class="bi bi-bell-slash text-muted" style="font-size: 2rem;"></i><p class="text-muted mt-2">Нет новых уведомлений</p></div>');
                                    }
                                }
                            }
                        });
                    } else {
                        // Если нет отдельного блока, скрываем только кнопку
                        button.fadeOut(300, function () {
                            $(this).remove();
                        });
                    }

                    // Принудительно обновляем счетчик после небольшой задержки
                    setTimeout(function () {
                        updateNotificationCount();
                        loadNotifications();
                    }, 100);
                }
            },
            error: function (xhr, status, error) {
                console.log('Ошибка AJAX:', xhr, status, error);
                console.log('Статус ответа:', xhr.status);
                console.log('Текст ответа:', xhr.responseText);

                if (xhr.status === 403) {
                    showAlert('Ошибка CSRF токена. Попробуйте обновить страницу.', 'danger');
                } else {
                    // В случае ошибки показываем уведомление пользователю
                    showAlert('Ошибка при отметке уведомления как прочитанного', 'danger');
                }
            }
        });
    });

    // Отметить все уведомления как прочитанные
    console.log('Регистрируем обработчик для .mark-all-read');
    $(document).on('click', '.mark-all-read', function () {
        console.log('Кнопка "Отметить все как прочитанные" нажата');
        var button = $(this);
        var cardBody = button.closest('.card').find('.card-body');
        var allNotifications = cardBody.find('.notification-item');

        console.log('Найдено уведомлений:', allNotifications.length);
        console.log('Кнопка найдена:', button.length > 0);
        console.log('Card body найдена:', cardBody.length > 0);

        if (allNotifications.length === 0) {
            showAlert('Нет уведомлений для отметки', 'info');
            return;
        }

        // Показываем индикатор загрузки
        button.prop('disabled', true).html('<i class="bi bi-hourglass-split"></i> Обработка...');

        // Получаем все ID уведомлений
        var notificationIds = [];
        allNotifications.each(function () {
            var markReadButton = $(this).find('.mark-read');
            var id = markReadButton.data('notification-id');
            console.log('Найден ID уведомления:', id);
            if (id) notificationIds.push(id);
        });

        console.log('Всего ID для отметки:', notificationIds);

        // Отправляем запрос для отметки всех уведомлений
        $.ajax({
            url: '/notifications/mark-all-read/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            data: JSON.stringify({
                notification_ids: notificationIds
            }),
            success: function (response) {
                console.log('Ответ сервера:', response);
                if (response.success) {
                    // Скрываем все уведомления
                    allNotifications.fadeOut(300, function () {
                        $(this).remove();

                        // Показываем сообщение об отсутствии уведомлений только в карточке уведомлений
                        var notificationsCard = $('#notifications-card');
                        if (notificationsCard.length > 0) {
                            var notificationsCardBody = notificationsCard.find('.card-body');
                            if (notificationsCardBody.length > 0) {
                                notificationsCardBody.html('<div class="text-center py-4"><i class="bi bi-bell-slash text-muted" style="font-size: 2rem;"></i><p class="text-muted mt-2">Нет новых уведомлений</p></div>');
                            }
                        }
                    });

                    // Скрываем кнопку "Отметить все как прочитанные"
                    button.fadeOut(300, function () {
                        $(this).remove();
                    });

                    showAlert('Все уведомления отмечены как прочитанные', 'success');

                    // Принудительно обновляем счетчик после небольшой задержки
                    setTimeout(function () {
                        updateNotificationCount();
                        loadNotifications();
                    }, 100);
                } else {
                    showAlert('Ошибка при отметке уведомлений: ' + (response.error || 'Неизвестная ошибка'), 'danger');
                }
            },
            error: function (xhr, status, error) {
                console.log('Ошибка AJAX:', xhr, status, error);
                console.log('Статус ответа:', xhr.status);
                console.log('Текст ответа:', xhr.responseText);
                showAlert('Ошибка при отметке уведомлений', 'danger');
            },
            complete: function () {
                button.prop('disabled', false).html('<i class="bi bi-check-all"></i> Отметить все как прочитанные');
            }
        });
    });

    // Обновление каждые 30 секунд
    setInterval(function () {
        updateNotificationCount();
        loadNotifications();
    }, 30000);

    // Инициализация
    updateNotificationCount();
    loadNotifications();

    // Дополнительная проверка привязки обработчика
    console.log('Количество кнопок .mark-all-read на странице:', $('.mark-all-read').length);
    $('.mark-all-read').each(function (index) {
        console.log('Кнопка', index + 1, 'найдена:', $(this).text().trim());

        // Добавляем обработчик напрямую к кнопке
        $(this).on('click', function (e) {
            e.preventDefault();
            console.log('Прямой обработчик сработал для кнопки', index + 1);

            // Вызываем основную логику
            var button = $(this);
            var cardBody = button.closest('.card').find('.card-body');
            var allNotifications = cardBody.find('.notification-item');

            console.log('Найдено уведомлений:', allNotifications.length);

            if (allNotifications.length === 0) {
                showAlert('Нет уведомлений для отметки', 'info');
                return;
            }

            // Показываем индикатор загрузки
            button.prop('disabled', true).html('<i class="bi bi-hourglass-split"></i> Обработка...');

            // Получаем все ID уведомлений
            var notificationIds = [];
            allNotifications.each(function () {
                var markReadButton = $(this).find('.mark-read');
                var id = markReadButton.data('notification-id');
                console.log('Найден ID уведомления:', id);
                if (id) notificationIds.push(id);
            });

            console.log('Всего ID для отметки:', notificationIds);

            // Отправляем запрос для отметки всех уведомлений
            $.ajax({
                url: '/notifications/mark-all-read/',
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json'
                },
                data: JSON.stringify({
                    notification_ids: notificationIds
                }),
                success: function (response) {
                    console.log('Ответ сервера:', response);
                    if (response.success) {
                        // Скрываем все уведомления
                        allNotifications.fadeOut(300, function () {
                            $(this).remove();

                            // Показываем сообщение об отсутствии уведомлений только в карточке уведомлений
                            var notificationsCard = $('#notifications-card');
                            if (notificationsCard.length > 0) {
                                var notificationsCardBody = notificationsCard.find('.card-body');
                                if (notificationsCardBody.length > 0) {
                                    notificationsCardBody.html('<div class="text-center py-4"><i class="bi bi-bell-slash text-muted" style="font-size: 2rem;"></i><p class="text-muted mt-2">Нет новых уведомлений</p></div>');
                                }
                            }
                        });

                        // Скрываем кнопку "Отметить все как прочитанные"
                        button.fadeOut(300, function () {
                            $(this).remove();
                        });

                        showAlert('Все уведомления отмечены как прочитанные', 'success');

                        // Принудительно обновляем счетчик после небольшой задержки
                        setTimeout(function () {
                            updateNotificationCount();
                            loadNotifications();
                        }, 100);
                    } else {
                        showAlert('Ошибка при отметке уведомлений: ' + (response.error || 'Неизвестная ошибка'), 'danger');
                    }
                },
                error: function (xhr, status, error) {
                    console.log('Ошибка AJAX:', xhr, status, error);
                    console.log('Статус ответа:', xhr.status);
                    console.log('Текст ответа:', xhr.responseText);
                    showAlert('Ошибка при отметке уведомлений', 'danger');
                },
                complete: function () {
                    button.prop('disabled', false).html('<i class="bi bi-check-all"></i> Отметить все как прочитанные');
                }
            });
        });
    });
}

// Обновление статуса заданий
function initTaskStatusUpdates() {
    $('.task-status-select').change(function () {
        var taskId = $(this).data('task-id');
        var newStatus = $(this).val();
        var select = $(this);

        // Показываем индикатор загрузки
        select.prop('disabled', true);
        select.after('<span class="loading ms-2"></span>');

        $.ajax({
            url: '/api/tasks/' + taskId + '/status/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            data: JSON.stringify({
                status: newStatus
            }),
            success: function (response) {
                if (response.success) {
                    // Обновляем бейдж статуса
                    var badge = select.closest('.task-item').find('.status-badge');
                    badge.removeClass().addClass('badge status-badge bg-' + getStatusColor(newStatus));
                    badge.text(getStatusText(newStatus));

                    // Показываем уведомление
                    showAlert('Статус задания обновлен', 'success');
                } else {
                    showAlert('Ошибка при обновлении статуса', 'danger');
                    // Возвращаем предыдущее значение
                    select.val(select.data('original-value'));
                }
            },
            error: function () {
                showAlert('Ошибка при обновлении статуса', 'danger');
                select.val(select.data('original-value'));
            },
            complete: function () {
                select.prop('disabled', false);
                select.siblings('.loading').remove();
            }
        });
    });
}

// Загрузка файлов
function initFileUploads() {
    $('.file-upload').change(function () {
        var file = this.files[0];
        var input = $(this);
        var preview = input.siblings('.file-preview');

        if (file) {
            // Показываем информацию о файле
            var fileInfo = $('<div class="file-info p-2 border rounded mb-2"></div>');
            fileInfo.html(
                '<i class="bi bi-file-earmark"></i> ' + file.name +
                ' <small class="text-muted">(' + formatFileSize(file.size) + ')</small>' +
                '<button type="button" class="btn btn-sm btn-outline-danger ms-2 remove-file">' +
                '<i class="bi bi-x"></i></button>'
            );

            preview.html(fileInfo);

            // Обработка удаления файла
            fileInfo.find('.remove-file').click(function () {
                input.val('');
                preview.empty();
            });
        }
    });
}

// Фильтры
function initFilters() {
    $('.filter-form').on('submit', function (e) {
        e.preventDefault();

        var form = $(this);
        var url = new URL(window.location);
        var formData = new FormData(form[0]);

        // Очищаем параметры URL
        url.search = '';

        // Добавляем параметры формы
        for (var pair of formData.entries()) {
            if (pair[1]) {
                url.searchParams.append(pair[0], pair[1]);
            }
        }

        // Переходим на новую страницу
        window.location.href = url.toString();
    });

    // Сброс фильтров
    $('.reset-filters').click(function () {
        window.location.href = window.location.pathname;
    });
}

// Подсказки
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initAutoRefresh() {
    // Автообновление каждые 5 минут (300000 мс), если пользователь не активен
    // Исключаем страницы с формами, чтобы не мешать пользователю
    const currentPath = window.location.pathname;

    const isFormPage = currentPath.includes('/create/') ||
        currentPath.includes('/edit/') ||
        currentPath.includes('/form/') ||
        currentPath.includes('/add/');

    const shouldAutoRefresh = (currentPath.includes('/shifts/') || currentPath.includes('/tasks/') ||
        currentPath.includes('/projects/') || currentPath.includes('/notes/') ||
        currentPath.includes('/materials/') || currentPath === '/');

    if ((currentPath.includes('/shifts/') || currentPath.includes('/tasks/') ||
        currentPath.includes('/projects/') || currentPath.includes('/notes/') ||
        currentPath.includes('/materials/') || currentPath === '/') && !isFormPage) {
        console.log('🔄 Автообновление включено (5 мин. неактивности)');
        let lastActivityTime = Date.now();

        // Обновляем метку времени при любой активности
        const activityEvents = ['mousemove', 'keydown', 'scroll', 'click', 'touchstart'];

        activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                lastActivityTime = Date.now();
            });
        });

        setInterval(function () {
            const now = Date.now();
            const inactiveTime = now - lastActivityTime;
            const remainingTime = 300000 - inactiveTime;
            const minutesLeft = Math.ceil(remainingTime / 60000);

            // Выводим информацию в консоль каждую минуту
            console.log(`🕐 Автообновление: ${minutesLeft} мин. до перезагрузки (неактивность: ${Math.round(inactiveTime / 1000)} сек.)`);

            // Проверяем, что вкладка активна и пользователь был неактивен как минимум 5 минут
            if (!document.hidden && inactiveTime >= 300000) {
                console.log('🔄 Автообновление страницы из-за неактивности');
                location.reload();
            }
        }, 60000); // Проверяем каждую минуту
    }
}


// Утилиты
function getCSRFToken() {
    var token = $('[name=csrfmiddlewaretoken]').val();
    if (!token) {
        token = $('meta[name=csrf-token]').attr('content');
    }
    console.log('CSRF Token found:', token);
    return token;
}

function showAlert(message, type) {
    var alert = $('<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        '</div>');

    $('.messages').append(alert);

    // Автоматически скрываем через 5 секунд
    setTimeout(function () {
        alert.alert('close');
    }, 5000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    var k = 1024;
    var sizes = ['B', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function getStatusColor(status) {
    var colors = {
        'pending': 'warning',
        'in_progress': 'info',
        'completed': 'success',
        'cancelled': 'danger'
    };
    return colors[status] || 'secondary';
}

function getStatusText(status) {
    var texts = {
        'pending': 'Ожидает',
        'in_progress': 'В работе',
        'completed': 'Завершено',
        'cancelled': 'Отменено'
    };
    return texts[status] || status;
}

function getPriorityColor(priority) {
    var colors = {
        1: 'success',
        2: 'info',
        3: 'warning',
        4: 'danger'
    };
    return colors[priority] || 'secondary';
}

// Экспорт в Excel
function exportToExcel(tableId, filename) {
    var table = document.getElementById(tableId);
    var wb = XLSX.utils.table_to_book(table, { sheet: "Sheet1" });
    XLSX.writeFile(wb, filename + '.xlsx');
}

// Экспорт в PDF
function exportToPDF(elementId, filename) {
    var element = document.getElementById(elementId);
    html2pdf().from(element).save(filename + '.pdf');
}

// Поиск
function initSearch() {
    $('.search-input').on('input', function () {
        var query = $(this).val().toLowerCase();
        var table = $(this).closest('.table-container').find('table tbody tr');

        table.each(function () {
            var text = $(this).text().toLowerCase();
            if (text.includes(query)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
}

// Сортировка таблиц
function initTableSorting() {
    $('.sortable').click(function () {
        var table = $(this).closest('table');
        var index = $(this).index();
        var rows = table.find('tbody tr').toArray();
        var ascending = $(this).hasClass('asc');

        rows.sort(function (a, b) {
            var aVal = $(a).find('td').eq(index).text();
            var bVal = $(b).find('td').eq(index).text();

            if (ascending) {
                return aVal.localeCompare(bVal);
            } else {
                return bVal.localeCompare(aVal);
            }
        });

        table.find('tbody').empty().append(rows);

        // Обновляем классы сортировки
        table.find('th').removeClass('asc desc');
        $(this).addClass(ascending ? 'desc' : 'asc');
    });
}

// Инициализация дополнительных функций
$(document).ready(function () {
    initSearch();
    initTableSorting();
});

// Переключение темы
function initThemeToggle() {
    // Загружаем сохраненную тему из localStorage
    var savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeIcon(savedTheme);
    }

    // Обработчик клика по переключателю темы
    $('#themeToggle').click(function () {
        var currentTheme = document.documentElement.getAttribute('data-theme');
        var newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        // Применяем новую тему
        document.documentElement.setAttribute('data-theme', newTheme);

        // Сохраняем в localStorage
        localStorage.setItem('theme', newTheme);

        // Обновляем иконку
        updateThemeIcon(newTheme);

        // Добавляем анимацию перехода
        $('body').addClass('theme-transition');
        setTimeout(function () {
            $('body').removeClass('theme-transition');
        }, 300);
    });
}

function updateThemeIcon(theme) {
    var icon = $('#themeIcon');
    if (theme === 'dark') {
        icon.removeClass('bi-sun-fill').addClass('bi-moon-fill');
    } else {
        icon.removeClass('bi-moon-fill').addClass('bi-sun-fill');
    }
} 