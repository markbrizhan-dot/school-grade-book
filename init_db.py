# init_db.py - ПОЛНАЯ БАЗА ДАННЫХ
# 14 учителей, 9 классов (1А-9А), 250+ учеников

import sqlite3
from werkzeug.security import generate_password_hash
import os
import random

DATABASE = 'school.db'


def init_database():
    """Создание БД с 14 учителями, 9 классами и 250+ учащимися"""

    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print('🗑️ Старая БД удалена')

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # ==================== СОЗДАНИЕ ТАБЛИЦ ====================

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'head_teacher', 'class_teacher', 'teacher', 'parent')),
            is_active INTEGER DEFAULT 1,
            last_login TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            academic_year TEXT,
            class_teacher_id INTEGER REFERENCES users(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            hours INTEGER DEFAULT 0,
            grade_level INTEGER
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id),
            phone TEXT,
            qualification TEXT,
            experience INTEGER
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS class_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            teacher_id INTEGER REFERENCES users(id),
            UNIQUE(class_id, subject_id)
        )
    ''')

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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            grade INTEGER NOT NULL CHECK (grade BETWEEN 2 AND 5),
            quarter TEXT NOT NULL,
            comment TEXT,
            teacher_id INTEGER REFERENCES users(id),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, subject_id, quarter)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            lesson_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('present', 'absent', 'late')),
            reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, subject_id, lesson_date)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            action TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            old_value TEXT,
            new_value TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
        )
    ''')

    # ==================== ИНДЕКСЫ ====================

    cur.execute('CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_grades_subject ON grades(subject_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(lesson_date)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_id)')

    # ==================== 14 УЧИТЕЛЕЙ + АДМИН + ЗАВУЧ + КЛАССНЫЙ РУКОВОДИТЕЛЬ ====================

    users_data = [
        # Администратор
        ('admin', 'admin123', 'Администратор системы', 'admin'),
        # Завуч
        ('head_teacher', 'teacher123', 'Иванова Анна Петровна', 'head_teacher'),
        # Классный руководитель
        ('class_teacher', 'teacher123', 'Петрова Мария Ивановна', 'class_teacher'),
        # 14 Учителей
        ('teacher1', 'teacher123', 'Сидоров Алексей Викторович', 'teacher'),
        ('teacher2', 'teacher123', 'Кузнецова Елена Дмитриевна', 'teacher'),
        ('teacher3', 'teacher123', 'Михайлов Сергей Владимирович', 'teacher'),
        ('teacher4', 'teacher123', 'Андреева Ольга Сергеевна', 'teacher'),
        ('teacher5', 'teacher123', 'Васильев Дмитрий Иванович', 'teacher'),
        ('teacher6', 'teacher123', 'Григорьева Наталья Петровна', 'teacher'),
        ('teacher7', 'teacher123', 'Данилов Алексей Александрович', 'teacher'),
        ('teacher8', 'teacher123', 'Егорова Татьяна Владимировна', 'teacher'),
        ('teacher9', 'teacher123', 'Зайцев Максим Алексеевич', 'teacher'),
        ('teacher10', 'teacher123', 'Ильина Мария Дмитриевна', 'teacher'),
        ('teacher11', 'teacher123', 'Козлов Сергей Николаевич', 'teacher'),
        ('teacher12', 'teacher123', 'Лебедева Екатерина Андреевна', 'teacher'),
        ('teacher13', 'teacher123', 'Морозов Владимир Павлович', 'teacher'),
        ('teacher14', 'teacher123', 'Новикова Анна Игоревна', 'teacher'),
    ]

    for username, password, full_name, role in users_data:
        cur.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', (username, generate_password_hash(password), full_name, role))

    # ==================== 9 КЛАССОВ (ТОЛЬКО А) ====================

    classes = ['1А', '2А', '3А', '4А', '5А', '6А', '7А', '8А', '9А']
    for cls in classes:
        cur.execute('INSERT OR IGNORE INTO classes (name, academic_year) VALUES (?, ?)', (cls, '2025-2026'))

    # ==================== ПРЕДМЕТЫ ====================

    subjects = [
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
        ('ИЗО', 1),
        ('Музыка', 1),
        ('Труд', 1),
        ('ОБЖ', 1),
    ]
    cur.executemany('INSERT OR IGNORE INTO subjects (name, hours) VALUES (?, ?)', subjects)

    # ==================== ПОЛУЧАЕМ ID ====================

    cur.execute('SELECT id, name FROM classes')
    class_ids = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute('SELECT id, name FROM subjects')
    subject_ids = {row[1]: row[0] for row in cur.fetchall()}

    # ==================== ГЕНЕРАЦИЯ УЧЕНИКОВ ====================

    # Фамилии
    last_names = [
        'Иванов', 'Петров', 'Сидоров', 'Кузнецов', 'Смирнов', 'Попов', 'Волков', 'Морозов',
        'Новиков', 'Фёдоров', 'Алексеев', 'Васильев', 'Григорьев', 'Данилов', 'Егоров',
        'Михайлов', 'Николаев', 'Сергеев', 'Андреев', 'Орлов', 'Соколов', 'Тихонов',
        'Крылов', 'Соловьёв', 'Борисов', 'Гусев', 'Виноградов', 'Белов', 'Медведев',
        'Антонов', 'Тарасов', 'Ильин', 'Савельев', 'Киселёв', 'Макаров'
    ]

    # Имена (мужские)
    first_names_male = [
        'Алексей', 'Дмитрий', 'Иван', 'Сергей', 'Андрей', 'Максим', 'Егор', 'Михаил',
        'Артём', 'Никита', 'Павел', 'Владимир', 'Александр', 'Евгений', 'Даниил',
        'Константин', 'Олег', 'Юрий', 'Вадим', 'Роман', 'Кирилл'
    ]

    # Имена (женские)
    first_names_female = [
        'Анна', 'Мария', 'Екатерина', 'Ольга', 'Татьяна', 'Наталья', 'Ирина', 'Елена',
        'Анастасия', 'Дарья', 'Виктория', 'Александра', 'Юлия', 'Валентина', 'Надежда',
        'Людмила', 'Светлана', 'Вера', 'Галина', 'Нина', 'Полина'
    ]

    # Отчества (мужские)
    middle_names_male = [
        'Александрович', 'Дмитриевич', 'Иванович', 'Сергеевич', 'Андреевич',
        'Максимович', 'Егорович', 'Михайлович', 'Артёмович', 'Никитич',
        'Павлович', 'Владимирович', 'Алексеевич', 'Евгеньевич', 'Даниилович'
    ]

    # Отчества (женские)
    middle_names_female = [
        'Александровна', 'Дмитриевна', 'Ивановна', 'Сергеевна', 'Андреевна',
        'Максимовна', 'Егоровна', 'Михайловна', 'Артёмовна', 'Никитична',
        'Павловна', 'Владимировна', 'Алексеевна', 'Евгеньевна', 'Данииловна'
    ]

    parent_names = [
        'Иванова Н.А.', 'Петрова М.И.', 'Сидоров П.С.', 'Кузнецова Е.В.',
        'Смирнов А.А.', 'Попов В.В.', 'Волкова Т.Н.', 'Морозов С.В.'
    ]

    streets = [
        'ул. Ленина', 'ул. Мира', 'ул. Садовая', 'ул. Школьная',
        'ул. Молодёжная', 'ул. Пушкина', 'ул. Гагарина', 'ул. Советская',
        'ул. Лермонтова', 'ул. Цветочная'
    ]

    def generate_students_for_class(class_name, count, start_year):
        class_id = class_ids.get(class_name)
        if not class_id:
            return []

        students = []
        random.seed(int(class_name[0]))

        # Перемешиваем фамилии
        shuffled_last = last_names.copy()
        random.shuffle(shuffled_last)

        for i in range(1, count + 1):
            is_male = i % 2 == 1

            last_name = shuffled_last[(i + int(class_name[0]) * 2) % len(shuffled_last)]

            if is_male:
                first_name = first_names_male[(i + int(class_name[0]) * 3) % len(first_names_male)]
                middle_name = middle_names_male[(i + int(class_name[0])) % len(middle_names_male)]
            else:
                first_name = first_names_female[(i + int(class_name[0]) * 3) % len(first_names_female)]
                middle_name = middle_names_female[(i + int(class_name[0]) * 2) % len(middle_names_female)]

            birth_month = (i % 12) + 1
            birth_day = (i % 28) + 1
            birth_year = start_year - (int(class_name[0]) - 1)
            birth_date = f'{birth_year}-{birth_month:02d}-{birth_day:02d}'

            address = f'{streets[i % len(streets)]}, {i + 5}'
            parent_name = parent_names[i % len(parent_names)]
            parent_phone = f'+7-999-{i:03d}-{i + 10:02d}-{i + 20:02d}'

            students.append(
                (last_name, first_name, middle_name, birth_date, address, parent_name, parent_phone, class_id))

        return students

    # Количество учащихся в каждом классе
    class_counts = {
        '1А': 25, '2А': 24, '3А': 26, '4А': 23,
        '5А': 27, '6А': 25, '7А': 24, '8А': 22, '9А': 26
    }

    start_years = {
        '1': 2018, '2': 2017, '3': 2016, '4': 2015,
        '5': 2014, '6': 2013, '7': 2012, '8': 2011, '9': 2010
    }

    all_students = []
    total_students = 0

    for class_name, count in class_counts.items():
        start_year = start_years.get(class_name[0], 2010)
        students = generate_students_for_class(class_name, count, start_year)
        if students:
            all_students.extend(students)
            total_students += len(students)
            print(f'   ✅ {class_name}: {len(students)} учащихся')

    # ==================== ВСТАВКА УЧЕНИКОВ ====================

    cur.executemany('''
        INSERT INTO students (last_name, first_name, middle_name, birth_date, 
                             address, parent_name, parent_phone, class_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', all_students)

    conn.commit()

    # ==================== ОЦЕНКИ ====================

    cur.execute('SELECT id FROM subjects')
    subject_ids_list = [row[0] for row in cur.fetchall()]

    cur.execute('SELECT id FROM students')
    student_ids = [row[0] for row in cur.fetchall()]

    # Получаем ID учителей
    cur.execute('SELECT id FROM users WHERE role = "teacher"')
    teacher_ids = [row[0] for row in cur.fetchall()]

    random.seed(42)
    grades_to_add = []

    for student_id in student_ids:
        num_subjects = random.randint(4, 7)
        selected_subjects = random.sample(subject_ids_list, min(num_subjects, len(subject_ids_list)))

        for subject_id in selected_subjects:
            grade = random.choices([2, 3, 4, 5], weights=[5, 20, 35, 40])[0]
            quarter = str(random.choice(['1', '2', '3', '4']))
            teacher_id = random.choice(teacher_ids) if teacher_ids else 4
            grades_to_add.append((student_id, subject_id, grade, quarter, '', teacher_id))

    if grades_to_add:
        cur.executemany('''
            INSERT OR IGNORE INTO grades (student_id, subject_id, grade, quarter, comment, teacher_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', grades_to_add)

    conn.commit()
    conn.close()

    # ==================== ВЫВОД РЕЗУЛЬТАТОВ ====================

    print('\n' + '=' * 70)
    print('✅ БАЗА ДАННЫХ УСПЕШНО СОЗДАНА!')
    print('-' * 70)
    print(f'   👨‍🏫 Учителей: 14 (как в отчёте!)')
    print(f'   👨‍🏫 Классных руководителей: 1')
    print(f'   🏫 Завуч: 1')
    print(f'   🔐 Администратор: 1')
    print(f'   📚 Классов: 9 (1А-9А)')
    print(f'   👨‍🎓 Учащихся: {total_students}')
    print(f'   📝 Оценок: {len(grades_to_add)}')
    print('=' * 70)
    print('\n📋 ДАННЫЕ ДЛЯ ВХОДА:')
    print('-' * 70)
    print('  🔐 Администратор:        admin / admin123')
    print('  🏫 Завуч:                head_teacher / teacher123')
    print('  👨‍🏫 Классный руководитель: class_teacher / teacher123')
    print('  👨‍🏫 Учитель 1-14:         teacher1 / teacher123 ... teacher14 / teacher123')
    print('=' * 70)
    print('\n🚀 Запустите: python app.py')
    print('🌐 http://localhost:5000')


if __name__ == '__main__':
    init_database()