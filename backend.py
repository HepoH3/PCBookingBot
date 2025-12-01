import sqlite3
import os

DB_FILE = os.getenv("PC_BOOKING_BOT_DB")
if not DB_FILE:
    raise ValueError("Установите переменную окружения PC_BOOKING_BOT_DB.")

ADMIN = os.getenv("PC_BOOKING_BOT_ADMIN")
if not ADMIN:
    raise ValueError("Установите переменную окружения PC_BOOKING_BOT_ADMIN.")

# Подключаемся к базе данных
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Инициализация таблицы пользователей
def init_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            role TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS computers (
            computer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            computer_number INTEGER UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            computer_id INTEGER,
            start_timestamp INTEGER,
            end_timestamp INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (computer_id) REFERENCES computers(computer_id)
        )
    ''')
    conn.commit()

# Инициализация администратора
def init_admin(bot_creator_username=ADMIN):
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, role)
        VALUES (?, 'administrator')
    ''', (bot_creator_username,))
    conn.commit()

# Функция для добавления стажера
def add_intern(username):
    try:
        cursor.execute('INSERT INTO users (username, role) VALUES (?, "intern")', (username,))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        return False
    return None

# Функция для добавления компьютера
def add_computer(computer_number):
    cursor.execute('INSERT INTO computers (computer_number) VALUES (?)', (computer_number,))
    conn.commit()

# Функция для удаления компьютера
def remove_computer(computer_number):
    cursor.execute('DELETE FROM computers WHERE computer_number = ?', (computer_number,))
    conn.commit()

# Функция для получения списка доступных компьютеров
def get_available_computers():
    cursor.execute('SELECT computer_id, computer_number FROM computers')
    return cursor.fetchall()

def get_computer_number(computer_id):
    cursor.execute('SELECT computer_number FROM computers WHERE computer_id = ?', (computer_id,))
    return cursor.fetchall()

# Функция для добавления пользователя в роль "руководитель"
def add_supervisor(username):
    # Проверяем, существует ли пользователь в базе данных
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        # Если пользователь существует, обновляем его роль
        cursor.execute('UPDATE users SET role = "supervisor" WHERE username = ?', (username,))
    else:
        # Если пользователя нет, добавляем его с ролью "руководитель"
        cursor.execute('INSERT INTO users (username, role) VALUES (?, "supervisor")', (username,))
    conn.commit()

# Функция для получения списка всех руководителей
def get_supervisors():
    cursor.execute('''
        SELECT user_id, username FROM users WHERE role = 'supervisor'
    ''')
    return cursor.fetchall()

# Функция для получения списка всех стажеров
def get_interns():
    cursor.execute('''
        SELECT user_id, username FROM users WHERE role = 'intern'
    ''')
    return cursor.fetchall()

# Функция для получения списка всех руководителей
def get_users():
    cursor.execute('''
        SELECT username FROM users
    ''')
    return cursor.fetchall()

# Функция для удаления пользователя (с запретом удаления администратора)
def delete_user(username):
    cursor.execute('''
        DELETE FROM users WHERE username = ? AND role != 'administrator'
    ''', (username,))
    conn.commit()

def get_user_id(username):
    # Запрос для получения user_id по username
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()  # Получаем первую запись

    if result:
        return result[0]  # Возвращаем user_id
    else:
        return None  # Если пользователь не найден, возвращаем None

def get_user_role(username):
    cursor.execute('SELECT role FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()

    if result:
        return result[0]  # Возвращаем user_id
    else:
        return None  # Если пользователь не найден, возвращаем None

# Функция проверки привилегий
def check_privileges(username, required_role):
    role_hierarchy = ['intern', 'supervisor', 'administrator']  # Определяем иерархию ролей
    user_role = get_user_role(username)

    if user_role:
        # Проверяем, находится ли роль пользователя выше или на том же уровне, что и требуемая роль
        return role_hierarchy.index(user_role) >= role_hierarchy.index(required_role)

    return False  # Пользователь не найден

def get_user_bookings(username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE user_id = ?", (get_user_id(username),))
    return cursor.fetchall()

def book_computer(user_id, computer_id, start_timestamp, end_timestamp):
    # Добавляем запись о бронировании
    cursor.execute("""
        INSERT INTO bookings (user_id, computer_id, start_timestamp, end_timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, computer_id, start_timestamp, end_timestamp))

    conn.commit()

def db_check_computer(computer_id, start_timestamp, end_timestamp):
    cursor.execute("""
        SELECT u.username
        FROM bookings AS b
        JOIN users AS u ON b.user_id = u.user_id
        WHERE b.computer_id = ?
            AND b.start_timestamp <= ?
            AND b.end_timestamp >= ?
    """, (computer_id, start_timestamp, end_timestamp))
    result = cursor.fetchone()              # Получаем первую запись, если она существует
    return result[0] if result else None    # Возвращаем username или None, если записи нет

def remove_booking(booking_id):
    try:
        # Проверяем, существует ли запись с данным ID
        cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        booking = cursor.fetchone()
        if booking is None:
            return False  # Бронирование с таким ID не найдено
        # Удаляем запись о бронировании
        cursor.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
        conn.commit()
        return True  # Бронирование успешно удалено
    except sqlite3.Error as e:
        print(f"Ошибка при удалении бронирования: {e}")
        return False

def check_available_computers(start_timestamp, end_timestamp):
    # Получаем все компьютеры
    cursor.execute("SELECT computer_id, computer_number FROM computers")
    all_computers = cursor.fetchall()

    available_computers = []

    for (computer_id, computer_number) in all_computers:
        # Проверяем, есть ли пересечения с существующими бронированиями
        cursor.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE computer_id = ? AND (
                (start_timestamp < ? AND end_timestamp > ?) OR
                (start_timestamp < ? AND end_timestamp > ?)
            )
        """, (computer_id, end_timestamp, start_timestamp, start_timestamp, end_timestamp))

        booking_count = cursor.fetchone()[0]

        # Если нет пересечений, добавляем компьютер в доступные
        if booking_count == 0:
            available_computers.append((computer_id, computer_number))

    return available_computers


# def delete_expired_bookings():
#     del_conn = sqlite3.connect('PCBooking.db')
#     del_cursor = del_conn.cursor()
#     while True:
#         # Удаляем записи, у которых время окончания меньше текущего времени
#         del_cursor.execute('DELETE FROM bookings WHERE end_timestamp < ?', (int(datetime.datetime.now().timestamp()),))
#         del_conn.commit()
#         # Ждем 10 минут перед следующей проверкой
#         time.sleep(600)  # 600 секунд