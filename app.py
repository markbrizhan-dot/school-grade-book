# app.py - SQLite версия (без PostgreSQL!)

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# ==================== РАБОТА С SQLite ====================

DATABASE = 'school.db'


def get_db():
    """Получение соединения с SQLite"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создание таблиц, если их нет"""
    conn = get_db()
    cur = conn.cursor()

    # Таблица пользователей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'head_teacher', 'class_teacher', 'teacher', 'parent')),
            is_active INTEGER DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица классов
    cur.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            academic_year TEXT,
            class_teacher_id INTEGER REFERENCES users(id)
        )
    ''')

    # Таблица предметов
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            hours INTEGER DEFAULT 0,
            grade_level INTEGER
        )
    ''')

    # Таблица учителей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id),
            phone TEXT,
            qualification TEXT,
            experience INTEGER
        )
    ''')

    # Таблица связи классов с предметами
    cur.execute('''
        CREATE TABLE IF NOT EXISTS class_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            teacher_id INTEGER REFERENCES users(id),
            UNIQUE(class_id, subject_id)
        )
    ''')

    # Таблица учащихся
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            birth_date TEXT,
            address TEXT,
            parent_name TEXT,
            parent_phone TEXT,
            class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица оценок
    cur.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            grade INTEGER NOT NULL CHECK (grade BETWEEN 2 AND 5),
            quarter TEXT NOT NULL,
            comment TEXT,
            teacher_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, subject_id, quarter)
        )
    ''')

    # Таблица посещаемости
    cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            lesson_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('present', 'absent', 'late')),
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, subject_id, lesson_date)
        )
    ''')

    # Таблица аудита
    cur.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            action TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            old_value TEXT,
            new_value TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
        )
    ''')

    # Создание индексов
    cur.execute('CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_grades_subject ON grades(subject_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(lesson_date)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_id)')

    # ==================== НАЧАЛЬНЫЕ ДАННЫЕ ====================

    # Администратор
    admin_password = generate_password_hash('admin123')
    cur.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
    ''', ('admin', admin_password, 'Администратор системы', 'admin'))

    # Завуч
    head_teacher_password = generate_password_hash('teacher123')
    cur.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
    ''', ('head_teacher', head_teacher_password, 'Иванова Анна Петровна', 'head_teacher'))

    # Классный руководитель
    class_teacher_password = generate_password_hash('teacher123')
    cur.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
    ''', ('class_teacher', class_teacher_password, 'Петрова Мария Ивановна', 'class_teacher'))

    # Учитель
    teacher_password = generate_password_hash('teacher123')
    cur.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
    ''', ('teacher', teacher_password, 'Сидоров Алексей Викторович', 'teacher'))

    # Классы
    classes_data = [
        ('1А', '2025-2026'),
        ('2А', '2025-2026'),
        ('3А', '2025-2026'),
        ('4А', '2025-2026'),
        ('5А', '2025-2026'),
        ('6А', '2025-2026'),
        ('7А', '2025-2026'),
        ('8А', '2025-2026'),
        ('9А', '2025-2026'),
    ]
    cur.executemany('INSERT OR IGNORE INTO classes (name, academic_year) VALUES (?, ?)', classes_data)

    # Предметы
    subjects_data = [
        ('Русский язык', 5),
        ('Математика', 5),
        ('Литература', 3),
        ('Английский язык', 3),
        ('Информатика', 2),
        ('Физика', 2),
        ('Химия', 2),
        ('Биология', 2),
        ('История', 2),
        ('Обществознание', 1),
        ('География', 2),
        ('Физическая культура', 2),
    ]
    cur.executemany('INSERT OR IGNORE INTO subjects (name, hours) VALUES (?, ?)', subjects_data)

    # Получаем ID 9А класса для тестовых учащихся
    cur.execute('SELECT id FROM classes WHERE name = ?', ('9А',))
    class_9a = cur.fetchone()

    if class_9a:
        class_id = class_9a[0]
        test_students = [
            ('Алексеев', 'Алексей', 'Александрович', '2010-05-15', 'ул. Ленина 10', 'Алексеева Н.А.',
             '+7-999-111-22-33'),
            ('Васильева', 'Анна', 'Ивановна', '2010-08-22', 'ул. Мира 5', 'Васильев И.П.', '+7-999-222-33-44'),
            ('Григорьев', 'Дмитрий', 'Петрович', '2010-12-03', 'ул. Садовая 15', 'Григорьева М.С.', '+7-999-333-44-55'),
        ]
        for student in test_students:
            cur.execute('''
                INSERT OR IGNORE INTO students (last_name, first_name, middle_name, birth_date, 
                                               address, parent_name, parent_phone, class_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*student, class_id))

    conn.commit()
    conn.close()
    print('✅ База данных SQLite успешно создана!')
    print('\n' + '=' * 60)
    print('📋 ДАННЫЕ ДЛЯ ВХОДА В СИСТЕМУ:')
    print('-' * 60)
    print('  🔐 Администратор:      admin / admin123')
    print('  🏫 Завуч:              head_teacher / teacher123')
    print('  👨‍🏫 Классный руководитель: class_teacher / teacher123')
    print('  👨‍🏫 Учитель:            teacher / teacher123')
    print('=' * 60)
    print('\n🚀 Запустите приложение командой: python app.py')
    print('🌐 Перейдите по адресу: http://localhost:5000')


# Инициализация БД при первом запуске
if not os.path.exists(DATABASE):
    init_db()

# Роли пользователей
ROLES = {
    'admin': 'Администратор',
    'head_teacher': 'Завуч',
    'class_teacher': 'Классный руководитель',
    'teacher': 'Учитель-предметник',
    'parent': 'Родитель'
}


# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Декоратор для проверки роли
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in allowed_roles:
                flash('У вас нет прав для доступа к этой странице', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Введите логин и пароль', 'danger')
            return render_template('login.html')

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'SELECT id, username, password_hash, role, full_name, last_login FROM users WHERE username = ?',
            (username,)
        )
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            # Обновляем время последнего входа
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                'UPDATE users SET last_login = ? WHERE id = ?',
                (datetime.now().isoformat(), user['id'])
            )
            conn.commit()
            conn.close()

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']

            flash(f'Добро пожаловать, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль', 'danger')

        return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Главная страница"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM students')
    students_count = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM teachers')
    teachers_count = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM classes')
    classes_count = cur.fetchone()[0]

    today = datetime.now().date().isoformat()
    cur.execute(
        'SELECT COUNT(*) FROM grades WHERE DATE(created_at) = ?',
        (today,)
    )
    grades_today = cur.fetchone()[0]

    cur.execute('''
        SELECT u.full_name, a.action, a.timestamp, a.table_name
        FROM audit_log a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
        LIMIT 10
    ''')
    recent_actions = cur.fetchall()

    conn.close()

    return render_template('dashboard.html',
                           students_count=students_count,
                           teachers_count=teachers_count,
                           classes_count=classes_count,
                           grades_today=grades_today,
                           recent_actions=recent_actions,
                           datetime=datetime)


@app.route('/students')
@login_required
@role_required(['admin', 'head_teacher', 'class_teacher', 'teacher'])
def students():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT id, name FROM classes ORDER BY name')
    classes = cur.fetchall()

    class_filter = request.args.get('class', '')

    if class_filter:
        cur.execute('''
            SELECT s.*, c.name as class_name
            FROM students s
            JOIN classes c ON s.class_id = c.id
            WHERE s.class_id = ?
            ORDER BY s.last_name, s.first_name
        ''', (class_filter,))
    else:
        cur.execute('''
            SELECT s.*, c.name as class_name
            FROM students s
            JOIN classes c ON s.class_id = c.id
            ORDER BY s.last_name, s.first_name
        ''')

    students = cur.fetchall()
    conn.close()

    return render_template('students.html',
                           students=students,
                           classes=classes,
                           selected_class=class_filter)


@app.route('/students/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_student():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM classes ORDER BY name')
    classes = cur.fetchall()
    conn.close()

    if request.method == 'POST':
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name')
        birth_date = request.form.get('birth_date')
        address = request.form.get('address')
        parent_name = request.form.get('parent_name')
        parent_phone = request.form.get('parent_phone')
        class_id = request.form.get('class_id')

        if not all([last_name, first_name, class_id]):
            flash('Заполните обязательные поля', 'danger')
            return render_template('add_student.html', classes=classes)

        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO students (last_name, first_name, middle_name, birth_date, 
                                address, parent_name, parent_phone, class_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (last_name, first_name, middle_name, birth_date, address,
              parent_name, parent_phone, class_id))
        student_id = cur.lastrowid
        conn.commit()

        cur.execute('''
            INSERT INTO audit_log (user_id, action, table_name, record_id, new_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], 'INSERT', 'students', student_id,
              json.dumps({'last_name': last_name, 'first_name': first_name})))
        conn.commit()
        conn.close()

        flash('Учащийся успешно добавлен', 'success')
        return redirect(url_for('students'))

    return render_template('add_student.html', classes=classes)


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_student(student_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cur.fetchone()

    cur.execute('SELECT id, name FROM classes ORDER BY name')
    classes = cur.fetchall()
    conn.close()

    if not student:
        flash('Учащийся не найден', 'danger')
        return redirect(url_for('students'))

    if request.method == 'POST':
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name')
        birth_date = request.form.get('birth_date')
        address = request.form.get('address')
        parent_name = request.form.get('parent_name')
        parent_phone = request.form.get('parent_phone')
        class_id = request.form.get('class_id')

        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            UPDATE students 
            SET last_name = ?, first_name = ?, middle_name = ?, 
                birth_date = ?, address = ?, parent_name = ?, 
                parent_phone = ?, class_id = ?
            WHERE id = ?
        ''', (last_name, first_name, middle_name, birth_date, address,
              parent_name, parent_phone, class_id, student_id))
        conn.commit()

        cur.execute('''
            INSERT INTO audit_log (user_id, action, table_name, record_id, new_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], 'UPDATE', 'students', student_id,
              json.dumps({'last_name': last_name, 'first_name': first_name})))
        conn.commit()
        conn.close()

        flash('Данные учащегося обновлены', 'success')
        return redirect(url_for('students'))

    return render_template('edit_student.html', student=student, classes=classes)


@app.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_student(student_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM grades WHERE student_id = ?', (student_id,))
    has_grades = cur.fetchone()[0] > 0

    if has_grades:
        flash('Невозможно удалить учащегося, так как у него есть оценки', 'danger')
    else:
        cur.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()

        cur.execute('''
            INSERT INTO audit_log (user_id, action, table_name, record_id)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], 'DELETE', 'students', student_id))
        conn.commit()
        flash('Учащийся удален', 'success')

    conn.close()
    return redirect(url_for('students'))


@app.route('/grades')
@login_required
@role_required(['admin', 'head_teacher', 'class_teacher', 'teacher'])
def grades():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT id, name FROM classes ORDER BY name')
    classes = cur.fetchall()

    cur.execute('SELECT id, name FROM subjects ORDER BY name')
    subjects = cur.fetchall()

    class_id = request.args.get('class_id', '')
    subject_id = request.args.get('subject_id', '')
    quarter = request.args.get('quarter', '')

    students_grades = []
    if class_id and subject_id and quarter:
        cur.execute('''
            SELECT 
                s.id, s.last_name, s.first_name, s.middle_name,
                g.grade, g.id as grade_id, g.comment, g.created_at
            FROM students s
            LEFT JOIN grades g ON g.student_id = s.id 
                AND g.subject_id = ? 
                AND g.quarter = ?
            WHERE s.class_id = ?
            ORDER BY s.last_name, s.first_name
        ''', (subject_id, quarter, class_id))
        students_grades = cur.fetchall()

    conn.close()

    return render_template('grades.html',
                           classes=classes,
                           subjects=subjects,
                           students_grades=students_grades,
                           selected_class=class_id,
                           selected_subject=subject_id,
                           selected_quarter=quarter)


@app.route('/grades/add', methods=['POST'])
@login_required
@role_required(['admin', 'head_teacher', 'class_teacher', 'teacher'])
def add_grade():
    student_id = request.form.get('student_id')
    subject_id = request.form.get('subject_id')
    grade = request.form.get('grade')
    quarter = request.form.get('quarter')
    comment = request.form.get('comment', '')
    class_id = request.form.get('class_id', '')

    if not all([student_id, subject_id, grade, quarter]):
        flash('Заполните все поля', 'danger')
        return redirect(url_for('grades'))

    try:
        grade_val = int(grade)
        if grade_val < 2 or grade_val > 5:
            flash('Оценка должна быть от 2 до 5', 'danger')
            return redirect(url_for('grades'))
    except ValueError:
        flash('Некорректная оценка', 'danger')
        return redirect(url_for('grades'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT id, grade FROM grades 
        WHERE student_id = ? AND subject_id = ? AND quarter = ?
    ''', (student_id, subject_id, quarter))
    existing = cur.fetchone()

    if existing:
        old_grade = existing[1]
        cur.execute('''
            UPDATE grades SET grade = ?, comment = ?, updated_at = ?
            WHERE id = ?
        ''', (grade, comment, datetime.now().isoformat(), existing[0]))
        action = 'UPDATE'
        old_value = json.dumps({'grade': old_grade})
        new_value = json.dumps({'grade': grade})
    else:
        cur.execute('''
            INSERT INTO grades (student_id, subject_id, grade, quarter, comment, teacher_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, subject_id, grade, quarter, comment, session['user_id']))
        action = 'INSERT'
        old_value = None
        new_value = json.dumps({'grade': grade})

    conn.commit()

    cur.execute('''
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_value, new_value)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], action, 'grades', student_id, old_value, new_value))
    conn.commit()
    conn.close()

    flash('Оценка успешно сохранена', 'success')
    return redirect(url_for('grades', class_id=class_id, subject_id=subject_id, quarter=quarter))


@app.route('/attendance')
@login_required
@role_required(['admin', 'head_teacher', 'class_teacher', 'teacher'])
def attendance():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT id, name FROM classes ORDER BY name')
    classes = cur.fetchall()

    cur.execute('SELECT id, name FROM subjects ORDER BY name')
    subjects = cur.fetchall()

    class_id = request.args.get('class_id', '')
    subject_id = request.args.get('subject_id', '')
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    students_attendance = []
    if class_id and subject_id:
        cur.execute('''
            SELECT 
                s.id, s.last_name, s.first_name, s.middle_name,
                a.id as attendance_id, a.status, a.reason, a.lesson_date
            FROM students s
            LEFT JOIN attendance a ON a.student_id = s.id 
                AND a.subject_id = ? 
                AND a.lesson_date = ?
            WHERE s.class_id = ?
            ORDER BY s.last_name, s.first_name
        ''', (subject_id, date_str, class_id))
        students_attendance = cur.fetchall()

    conn.close()

    return render_template('attendance.html',
                           classes=classes,
                           subjects=subjects,
                           students_attendance=students_attendance,
                           selected_class=class_id,
                           selected_subject=subject_id,
                           selected_date=date_str)


@app.route('/attendance/mark', methods=['POST'])
@login_required
@role_required(['admin', 'head_teacher', 'class_teacher', 'teacher'])
def mark_attendance():
    student_id = request.form.get('student_id')
    subject_id = request.form.get('subject_id')
    lesson_date = request.form.get('lesson_date')
    status = request.form.get('status')
    reason = request.form.get('reason', '')
    class_id = request.form.get('class_id', '')

    if not all([student_id, subject_id, lesson_date, status]):
        flash('Заполните все поля', 'danger')
        return redirect(url_for('attendance'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT id FROM attendance 
        WHERE student_id = ? AND subject_id = ? AND lesson_date = ?
    ''', (student_id, subject_id, lesson_date))
    existing = cur.fetchone()

    if existing:
        cur.execute('''
            UPDATE attendance SET status = ?, reason = ?, updated_at = ?
            WHERE id = ?
        ''', (status, reason, datetime.now().isoformat(), existing[0]))
        action = 'UPDATE'
    else:
        cur.execute('''
            INSERT INTO attendance (student_id, subject_id, lesson_date, status, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, subject_id, lesson_date, status, reason))
        action = 'INSERT'

    conn.commit()

    cur.execute('''
        INSERT INTO audit_log (user_id, action, table_name, record_id, new_value)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], action, 'attendance', student_id,
          json.dumps({'status': status, 'reason': reason})))
    conn.commit()
    conn.close()

    flash('Посещаемость отмечена', 'success')
    return redirect(url_for('attendance', class_id=class_id, subject_id=subject_id, date=lesson_date))


@app.route('/reports')
@login_required
@role_required(['admin', 'head_teacher', 'class_teacher'])
def reports():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM classes ORDER BY name')
    classes = cur.fetchall()
    conn.close()
    return render_template('reports.html', classes=classes)


@app.route('/reports/generate', methods=['POST'])
@login_required
@role_required(['admin', 'head_teacher', 'class_teacher'])
def generate_report():
    report_type = request.form.get('report_type')
    class_id = request.form.get('class_id')
    quarter = request.form.get('quarter')

    if not report_type or not class_id or not quarter:
        flash('Заполните все поля', 'danger')
        return redirect(url_for('reports'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT name FROM classes WHERE id = ?', (class_id,))
    class_name = cur.fetchone()[0]

    cur.execute('''
        SELECT 
            s.id, s.last_name, s.first_name, s.middle_name,
            AVG(g.grade) as average_grade,
            COUNT(g.id) as grades_count
        FROM students s
        LEFT JOIN grades g ON g.student_id = s.id AND g.quarter = ?
        WHERE s.class_id = ?
        GROUP BY s.id, s.last_name, s.first_name, s.middle_name
        ORDER BY s.last_name, s.first_name
    ''', (quarter, class_id))
    students = cur.fetchall()

    conn.close()

    report = {
        'class_name': class_name,
        'quarter': quarter,
        'generated_at': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'students': students
    }

    return render_template('report_result.html', report=report)


@app.route('/users')
@login_required
@role_required(['admin'])
def users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, username, full_name, role, last_login, is_active
        FROM users
        ORDER BY username
    ''')
    users = cur.fetchall()
    conn.close()
    return render_template('users.html', users=users, roles=ROLES)


@app.route('/users/add', methods=['POST'])
@login_required
@role_required(['admin'])
def add_user():
    username = request.form.get('username')
    full_name = request.form.get('full_name')
    role = request.form.get('role')
    password = request.form.get('password')

    if not all([username, full_name, role, password]):
        flash('Заполните все поля', 'danger')
        return redirect(url_for('users'))

    if len(password) < 6:
        flash('Пароль должен быть не менее 6 символов', 'danger')
        return redirect(url_for('users'))

    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(password)

    try:
        cur.execute('''
            INSERT INTO users (username, full_name, role, password_hash)
            VALUES (?, ?, ?, ?)
        ''', (username, full_name, role, password_hash))
        user_id = cur.lastrowid
        conn.commit()

        cur.execute('''
            INSERT INTO audit_log (user_id, action, table_name, record_id, new_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], 'INSERT', 'users', user_id,
              json.dumps({'username': username, 'role': role})))
        conn.commit()
        flash('Пользователь успешно добавлен', 'success')
    except sqlite3.IntegrityError:
        flash('Пользователь с таким логином уже существует', 'danger')
    finally:
        conn.close()

    return redirect(url_for('users'))


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('Нельзя удалить самого себя', 'danger')
        return redirect(url_for('users'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()

    cur.execute('''
        INSERT INTO audit_log (user_id, action, table_name, record_id)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], 'DELETE', 'users', user_id))
    conn.commit()
    conn.close()

    flash('Пользователь удален', 'success')
    return redirect(url_for('users'))


@app.route('/profile')
@login_required
def profile():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, username, full_name, role, last_login
        FROM users WHERE id = ?
    ''', (session['user_id'],))
    user = cur.fetchone()
    conn.close()
    return render_template('profile.html', user=user, roles=ROLES)


@app.route('/profile/change_password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not all([old_password, new_password, confirm_password]):
        flash('Заполните все поля', 'danger')
        return redirect(url_for('profile'))

    if new_password != confirm_password:
        flash('Пароли не совпадают', 'danger')
        return redirect(url_for('profile'))

    if len(new_password) < 6:
        flash('Новый пароль должен быть не менее 6 символов', 'danger')
        return redirect(url_for('profile'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT password_hash FROM users WHERE id = ?', (session['user_id'],))
    user = cur.fetchone()

    if not check_password_hash(user[0], old_password):
        flash('Неверный текущий пароль', 'danger')
        conn.close()
        return redirect(url_for('profile'))

    new_hash = generate_password_hash(new_password)
    cur.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, session['user_id']))
    conn.commit()
    conn.close()

    flash('Пароль успешно изменен', 'success')
    return redirect(url_for('profile'))


if __name__ == '__main__':
    # Проверяем наличие БД, если нет - создаем
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)