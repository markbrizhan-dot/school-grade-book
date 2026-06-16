// static/js/scripts.js - Дополнительные JavaScript скрипты

// ============================================================
// ОБЩИЕ УТИЛИТЫ
// ============================================================

/**
 * Автоматическое скрытие flash-сообщений через заданное время
 * @param {number} timeout - Время в миллисекундах (по умолчанию 5000)
 */
function autoHideAlerts(timeout = 5000) {
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(el => {
            const alert = new bootstrap.Alert(el);
            alert.close();
        });
    }, timeout);
}

// Запускаем автоскрытие после загрузки страницы
document.addEventListener('DOMContentLoaded', autoHideAlerts);

// ============================================================
// ПОДТВЕРЖДЕНИЕ ДЕЙСТВИЙ
// ============================================================

/**
 * Подтверждение удаления
 * @param {string} message - Сообщение для подтверждения
 * @returns {boolean}
 */
function confirmDelete(message = 'Вы уверены, что хотите удалить эту запись?') {
    return confirm(message);
}

/**
 * Подтверждение смены статуса
 * @param {string} message - Сообщение для подтверждения
 * @returns {boolean}
 */
function confirmAction(message = 'Вы уверены, что хотите выполнить это действие?') {
    return confirm(message);
}

// ============================================================
// РАБОТА С ФОРМАМИ
// ============================================================

/**
 * Валидация формы перед отправкой
 * @param {string} formId - ID формы
 * @returns {boolean}
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const inputs = form.querySelectorAll('[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Очистка полей формы
 * @param {string} formId - ID формы
 */
function resetForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.reset();
    form.querySelectorAll('.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
}

// ============================================================
// РАБОТА С ТАБЛИЦАМИ
// ============================================================

/**
 * Фильтрация таблицы по тексту
 * @param {string} inputId - ID поля ввода
 * @param {string} tableId - ID таблицы
 */
function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    const filter = input.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

/**
 * Сортировка таблицы по колонке
 * @param {string} tableId - ID таблицы
 * @param {number} columnIndex - Индекс колонки
 */
function sortTable(tableId, columnIndex) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Определяем направление сортировки
    const isAsc = table.dataset.sortAsc === 'true';
    
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex]?.textContent.trim() || '';
        const bText = b.cells[columnIndex]?.textContent.trim() || '';
        return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });
    
    // Переворачиваем направление для следующего клика
    table.dataset.sortAsc = !isAsc;
    
    // Перерисовываем таблицу
    rows.forEach(row => tbody.appendChild(row));
}

// ============================================================
// РАБОТА С ДАТАМИ
// ============================================================

/**
 * Форматирование даты в локальный формат
 * @param {string|Date} date - Дата
 * @param {string} format - Формат ('short', 'long', 'time')
 * @returns {string}
 */
function formatDate(date, format = 'short') {
    const d = new Date(date);
    if (isNaN(d.getTime())) return '';
    
    const options = {
        short: { day: '2-digit', month: '2-digit', year: 'numeric' },
        long: { day: '2-digit', month: 'long', year: 'numeric' },
        time: { hour: '2-digit', minute: '2-digit' }
    };
    
    return d.toLocaleDateString('ru-RU', options[format] || options.short);
}

/**
 * Получение текущей даты в формате YYYY-MM-DD
 * @returns {string}
 */
function getTodayString() {
    const today = new Date();
    return today.toISOString().split('T')[0];
}

// ============================================================
// РАБОТА С ОЦЕНКАМИ
// ============================================================

/**
 * Получение цвета для оценки
 * @param {number} grade - Оценка (2-5)
 * @returns {string} - CSS класс
 */
function getGradeColor(grade) {
    const colors = {
        5: 'success',
        4: 'primary',
        3: 'warning',
        2: 'danger'
    };
    return colors[grade] || 'secondary';
}

/**
 * Получение текстового статуса для оценки
 * @param {number} grade - Оценка (2-5)
 * @returns {string}
 */
function getGradeText(grade) {
    const texts = {
        5: 'Отлично',
        4: 'Хорошо',
        3: 'Удовлетворительно',
        2: 'Неудовлетворительно'
    };
    return texts[grade] || '—';
}

// ============================================================
// РАБОТА С ПОСЕЩАЕМОСТЬЮ
// ============================================================

/**
 * Получение статуса посещаемости
 * @param {string} status - Статус ('present', 'absent', 'late')
 * @returns {Object} - { class, text }
 */
function getAttendanceStatus(status) {
    const statuses = {
        'present': { class: 'success', text: 'Присутствовал' },
        'absent': { class: 'danger', text: 'Отсутствовал' },
        'late': { class: 'warning', text: 'Опоздал' }
    };
    return statuses[status] || { class: 'secondary', text: 'Не отмечено' };
}

// ============================================================
// РАБОТА С ОТЧЕТАМИ
// ============================================================

/**
 * Печать отчета
 */
function printReport() {
    window.print();
}

/**
 * Экспорт таблицы в CSV
 * @param {string} tableId - ID таблицы
 * @param {string} filename - Имя файла
 */
function exportToCSV(tableId, filename = 'report.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            let text = col.textContent.trim();
            // Экранируем кавычки
            text = text.replace(/"/g, '""');
            // Добавляем в кавычки если есть запятая
            if (text.includes(',')) {
                text = `"${text}"`;
            }
            rowData.push(text);
        });
        csv.push(rowData.join(','));
    });
    
    // Создаем и скачиваем файл
    const blob = new Blob(['\uFEFF' + csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ============================================================
// РАБОТА С API
// ============================================================

/**
 * Отправка AJAX запроса
 * @param {string} url - URL запроса
 * @param {Object} data - Данные для отправки
 * @param {string} method - HTTP метод
 * @returns {Promise}
 */
async function sendRequest(url, data = null, method = 'GET') {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Ошибка запроса:', error);
        throw error;
    }
}

/**
 * Обновление данных без перезагрузки страницы
 * @param {string} url - URL для обновления
 * @param {string} targetId - ID элемента для обновления
 */
async function refreshData(url, targetId) {
    try {
        const response = await fetch(url);
        const html = await response.text();
        const target = document.getElementById(targetId);
        if (target) {
            target.innerHTML = html;
        }
    } catch (error) {
        console.error('Ошибка обновления данных:', error);
    }
}

// ============================================================
// ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ
// ============================================================

/**
 * Дебаунс для ограничения частоты вызовов
 * @param {Function} func - Функция
 * @param {number} wait - Задержка в миллисекундах
 * @returns {Function}
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Копирование текста в буфер обмена
 * @param {string} text - Текст для копирования
 * @returns {Promise}
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Скопировано в буфер обмена', 'success');
    } catch (err) {
        console.error('Ошибка копирования:', err);
        showToast('Не удалось скопировать текст', 'danger');
    }
}

/**
 * Показ тост-уведомления
 * @param {string} message - Сообщение
 * @param {string} type - Тип ('success', 'danger', 'warning', 'info')
 */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0 show`;
    toast.role = 'alert';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Автоматическое скрытие через 3 секунды
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Создание контейнера для тост-уведомлений
 * @returns {HTMLElement}
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ============================================================
// ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Добавляем класс для анимации карточек
    document.querySelectorAll('.card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 + index * 50);
    });
    
    // Автофокус на первое поле ввода, если оно есть
    const firstInput = document.querySelector('input:not([readonly])');
    if (firstInput && !document.querySelector('.alert')) {
        // Не ставим фокус на странице входа
        if (!window.location.pathname.includes('login')) {
            firstInput.focus();
        }
    }
    
    console.log('✅ Система управления успеваемостью загружена');
    console.log(`📅 ${new Date().toLocaleString('ru-RU')}`);
});

// ============================================================
// ОБРАБОТЧИКИ СОБЫТИЙ
// ============================================================

// Подтверждение удаления для всех форм с классом .confirm-delete
document.addEventListener('click', function(e) {
    if (e.target.closest('.confirm-delete')) {
        if (!confirm('Вы уверены, что хотите удалить эту запись?')) {
            e.preventDefault();
        }
    }
});

// Подтверждение действия для всех форм с классом .confirm-action
document.addEventListener('click', function(e) {
    if (e.target.closest('.confirm-action')) {
        if (!confirm('Вы уверены, что хотите выполнить это действие?')) {
            e.preventDefault();
        }
    }
});

// Автоматическая валидация форм
document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.hasAttribute('data-validate')) {
        const required = form.querySelectorAll('[required]');
        let isValid = true;
        
        required.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            showToast('Заполните все обязательные поля', 'warning');
        }
    }
});