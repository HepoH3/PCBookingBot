import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import time
import pytz
from backend import *
# import threading

# Задаем рабочий часовой пояс
moscow_tz = pytz.timezone("Europe/Moscow")

# Обработчик команды /addintern
async def addintern(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    user_usernames = context.args  # Список имен пользователей
    skipped_usernames = []
    registered_usernames = []
    if check_privileges(username, 'supervisor'):
        for user_username in user_usernames:
            if user_username[0] == '@':
                user_username = user_username[1:]
            if add_intern(user_username):
                registered_usernames.append(user_username)
            else:
                skipped_usernames.append(user_username)
        msg = ""
        if registered_usernames:
            msg += f"Пользователи {', '.join(registered_usernames)} теперь стажеры."
        if skipped_usernames:
            msg += f"\nПользователи {', '.join(skipped_usernames)} уже зарегистрированы."
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Неизвестная или недоступная команда.")

# Обработчик команды /addsuper
async def addsuper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    user_usernames = context.args  # Список имен пользователей

    if check_privileges(username, 'administrator'):
        for user_username in user_usernames:
            if user_username[0] == '@':
                user_username = user_username[1:]
            add_supervisor(user_username)
        await update.message.reply_text(f"Пользователи {', '.join(user_usernames)} теперь руководители.")
    else:
        await update.message.reply_text("Неизвестная или недоступная команда.")

# Обработчик команды /listsupers
async def listsupers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    if check_privileges(username, 'administrator'):
        supervisors = get_supervisors()
        if supervisors:
            supervisors_list = "\n".join([f"ID: {sup[0]}, Username: {sup[1]}" for sup in supervisors])
            await update.message.reply_text(f"Список руководителей:\n{supervisors_list}")
        else:
            await update.message.reply_text("Руководители не найдены.")
    else:
        await update.message.reply_text("Неизвестная или недоступная команда.")

# Обработчик команды /listusers
async def listusers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    if check_privileges(username, 'administrator'):
        users = get_users()
        if users:
            users_list = "\n".join([f"{usr[0]}" for usr in users])
            await update.message.reply_text(users_list)
        else:
            await update.message.reply_text("Пользователи не найдены.")
    else:
        await update.message.reply_text("Неизвестная или недоступная команда.")

# Обработчик команды /deluser
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    if check_privileges(username, 'administrator'):
        if not context.args:
            await update.message.reply_text("Нужно указать удаляемого пользователя.")
            return

        user_username = context.args[0]
        if user_username[0] == '@':
            user_username = user_username[1:]
        # Проверка запрета удаления администратора
        if check_privileges(user_username, 'administrator'):
            await update.message.reply_text("Удаление администратора запрещено.")
        else:
            delete_user(user_username)
            await update.message.reply_text(f"Пользователь {user_username} удален.")
    else:
        await update.message.reply_text("Неизвестная или недоступная команда.")

# Обработчик команды /addcomputer
async def addcomputer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    if check_privileges(username, 'supervisor'):
        if not context.args:
            await update.message.reply_text("Нужно указать список компьютеров.")
            return

        added_computers = []
        for computer_number in context.args:
            add_computer(computer_number)
            added_computers.append(computer_number)

        await update.message.reply_text(f"Компьютеры {', '.join(added_computers)} добавлены.")
    else:
        await update.message.reply_text("Неизвестная или недоступная команда.")

# Обработчик команды /removecomputer
async def removecomputer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    if check_privileges(username, 'supervisor'):
        if not context.args:
            await update.message.reply_text("Нужно указать список компьютеров.")
            return

        removed_computers = []
        for computer_number in context.args:
            remove_computer(computer_number)
            removed_computers.append(computer_number)

        await update.message.reply_text(f"Компьютеры {', '.join(removed_computers)} удалены.")
    else:
        await update.message.reply_text("Неизвестная или недоступная команда.")

# Обработчик команды /listcomputers
async def listcomputers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    if check_privileges(username, 'supervisor'):
        computers = [computer[1] for computer in get_available_computers()]
        if computers:
            computers_list = "\n".join([str(comp[0]) for comp in computers])
            await update.message.reply_text(f"Доступные к бронированию компьютеры:\n{computers_list}")
        else:
            await update.message.reply_text("Нет доступных для бронирования компьютеров")
    else:
        await update.message.reply_text("Неизвестная или недоступная команда.")

# Обработчик команды /checkcomputer
async def check_computer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    context.user_data["scenario"] = "check"
    if not check_privileges(username, 'intern'):
        await update.message.reply_text("Неизвестная или недоступная команда.")
        return

    # Получаем следующие 6 рабочих дней
    working_days = get_next_working_days()

    # Создаем клавиатуру для выбора даты
    keyboard = [[InlineKeyboardButton(day.strftime("%Y-%m-%d"), callback_data=f"check {str(day)}")] for day in working_days]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите дату:", reply_markup=reply_markup)

# Временные интервалы
time_slots = [
    ("09:00", "10:30"),
    ("10:30", "12:30"),
    ("12:30", "14:00"),
    ("14:00", "15:30"),
    ("15:30", "17:00"),
    ("17:00", "18:30"),
    ("18:30", "20:00"),
    ("20:00", "21:30"),
]

# Функция для получения рабочих дней
def get_next_working_days():
    moscow_today = datetime.datetime.now(moscow_tz).date()
    working_days = []
    while len(working_days) < 6:
        if moscow_today.weekday() < 6:  # Пн-Сб
            working_days.append(moscow_today)
        moscow_today += datetime.timedelta(days=1)
    return working_days

# Обработчик команды /book
async def book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    context.user_data["scenario"] = "book"
    if not check_privileges(username, 'intern'):
        await update.message.reply_text("Неизвестная или недоступная команда.")
        return

    # Получаем следующие 6 рабочих дней
    working_days = get_next_working_days()

    # Создаем клавиатуру для выбора даты
    keyboard = [[InlineKeyboardButton(day.strftime("%Y-%m-%d"), callback_data=f"book {str(day)}")] for day in working_days]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите дату:", reply_markup=reply_markup)

# Обработчик выбора даты
async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    start_slot_index = 0
    selected_date = datetime.datetime.strptime(query.data[5:], "%Y-%m-%d").date()
    if selected_date == datetime.datetime.now().date():
        for i, slot in enumerate(time_slots):
            slot_end_time = slot[1].split(":")
            cur_time      = datetime.datetime.now(moscow_tz).strftime("%H:%M").split(":")
            slot_end_stamp = int(slot_end_time[0])*60 + int(slot_end_time[1])
            cur_time_stamp = int(cur_time[0])*60 + int(cur_time[1])
            if slot_end_stamp > cur_time_stamp:
                start_slot_index = i
                break
    start_slots = time_slots[start_slot_index:]
    # Выводим временные интервалы
    keyboard = [[InlineKeyboardButton(f"{start} - {end}", callback_data=f"book {selected_date} {start_slot_index+i}")] for i, (start, end) in enumerate(start_slots)]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=f"Выбрана дата {selected_date}. Выберите время начала брони:", reply_markup=reply_markup)

# Обработчик выбора временного интервала
async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split()

    selected_date = data[1]
    if context.user_data["scenario"] == "book":
        start_slot_index = int(data[2])
    else:
        start_slot_index = 0

    # Создаем клавиатуру для выбора конечного интервала
    end_slots = time_slots[start_slot_index:]  # Оставшиеся интервалы

    if context.user_data["scenario"] == "book":
        keyboard = [[InlineKeyboardButton(f"{start} - {end}", callback_data=f"book {selected_date} {start_slot_index} {i}")] for i, (start, end) in enumerate(end_slots, start=start_slot_index)]
    else:
        keyboard = [[InlineKeyboardButton(f"{start} - {end}", callback_data=f"check {selected_date} {i}")] for i, (start, end) in enumerate(end_slots, start=start_slot_index)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if context.user_data["scenario"] == "book":
        await query.edit_message_text(text=f"Выбрано время {time_slots[start_slot_index][0]} - {time_slots[start_slot_index][1]}. Выберите время окончания брони:", reply_markup=reply_markup)
    else:
        await query.edit_message_text(text=f"Выберите проверяемое время:", reply_markup=reply_markup)

# Обработчик выбора конечного интервала
async def handle_end_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split()

    selected_date = data[1]
    start_slot_index = int(data[2])
    if context.user_data["scenario"] == "book":
        end_slot_index = int(data[3])
    else:
        end_slot_index = int(data[2])

    start_time = time_slots[start_slot_index][0]
    end_time = time_slots[end_slot_index][1]

    # Рассчитываем timestamps
    date_object = datetime.datetime.strptime(selected_date, "%Y-%m-%d")
    date_object = moscow_tz.localize(date_object)
    start_timestamp = int(date_object.replace(hour=int(start_time.split(':')[0]), minute=int(start_time.split(':')[1]), second=0).timestamp())
    end_timestamp = int(date_object.replace(hour=int(end_time.split(':')[0]), minute=int(end_time.split(':')[1]), second=0).timestamp())

    if context.user_data["scenario"] == "book":
        # Проверяем доступность компьютеров
        available_computers = check_available_computers(start_timestamp, end_timestamp)

        if available_computers:
            keyboard = [[InlineKeyboardButton(f"Компьютер {computer_number}", callback_data=f"{computer_id} {computer_number} {start_timestamp} {end_timestamp}")] for (computer_id, computer_number) in available_computers]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(text="Доступные компьютеры:", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text="В указанный промежуток времени нет доступных компьютеров.")
    else:
        available_computers = get_available_computers()
        keyboard = [[InlineKeyboardButton(f"Компьютер {computer_number}", callback_data=f"{computer_id} {computer_number} {start_timestamp} {end_timestamp}")] for (computer_id, computer_number) in available_computers]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Выберите компьютер для проверки:", reply_markup=reply_markup)

async def handle_computer_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split()

    computer_id = int(data[0])
    computer_number = int(data[1])
    start_timestamp = int(data[2])
    end_timestamp = int(data[3])
    if context.user_data["scenario"] == "book":
        user_id = get_user_id(update.effective_user.username)

        # Бронируем компьютер
        book_computer(user_id, computer_id, start_timestamp, end_timestamp)

        await query.edit_message_text(text=f"Забронирован компьютер {computer_number} на время: {datetime.datetime.fromtimestamp(start_timestamp, tz=pytz.UTC).astimezone(moscow_tz).strftime('%Y-%m-%d %H:%M')} - {datetime.datetime.fromtimestamp(end_timestamp, tz=pytz.UTC).astimezone(moscow_tz).strftime('%H:%M')}.")
    else:
        booked_user = db_check_computer(computer_id, start_timestamp, end_timestamp)
        if booked_user:
            await query.edit_message_text(text=f"В указанное время Компьютер {computer_id} забронирован пользователем @{booked_user}.")
        else:
            await query.edit_message_text(text=f"В указанное время Компьютер {computer_id} свободен.")


# Основная функция для обработки команды /listbookings
async def list_bookings(update: Update, context: CallbackContext):
    # Если передан аргумент (имя пользователя)
    if context.args:
        if not check_privileges(update.message.from_user.username, 'supervisor'):
            await update.message.reply_text("У вас недостаточно прав для выполнения этой операции.")
            return

        target_username = context.args[0]
        bookings = get_user_bookings(target_username)

        if not bookings:
            await update.message.reply_text(f"У пользователя {target_username} нет активных бронирований.")
            return

        # Формирование кнопок для отмены бронирований
        keyboard = []
        for booking in bookings:

            text = f"Компьютер {get_computer_number(booking[2])[0][0]}: {datetime.datetime.fromtimestamp(booking[3], tz=pytz.UTC).astimezone(moscow_tz).strftime('%Y-%m-%d %H:%M')} - {datetime.datetime.fromtimestamp(booking[4], tz=pytz.UTC).astimezone(moscow_tz).strftime('%H:%M')}"
            callback_data = f"cancel_{booking[0]}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Бронирования пользователя {target_username}:", reply_markup=reply_markup)

    # Если аргументы не переданы — выводим бронирования текущего пользователя
    else:
        username = update.message.from_user.username

        if not check_privileges(username, 'intern'):
            await update.message.reply_text("У вас недостаточно прав для выполнения этой операции.")
            return

        bookings = get_user_bookings(username)

        # Формирование кнопок для отмены бронирований
        keyboard = []
        for booking in bookings:
            if booking[4] > int(datetime.datetime.now().timestamp()):
                text = f"Компьютер {get_computer_number(booking[2])[0][0]}: {datetime.datetime.fromtimestamp(booking[3], tz=pytz.UTC).astimezone(moscow_tz).strftime('%Y-%m-%d %H:%M')} - {datetime.datetime.fromtimestamp(booking[4], tz=pytz.UTC).astimezone(moscow_tz).strftime('%H:%M')}"
                callback_data = f"cancel_{booking[0]}"
                keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])

        if not keyboard:
            await update.message.reply_text("У вас нет активных бронирований.")
            return

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Ваши текущие бронирования:", reply_markup=reply_markup)


# Функция для обработки нажатия на кнопку и отмены бронирования
async def cancel_booking_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    # Получение ID бронирования из callback_data
    booking_id = query.data.split('_')[1]
    success = remove_booking(booking_id)

    if success:
        await query.edit_message_text(f"Бронирование {booking_id} успешно отменено.")
    else:
        await query.edit_message_text(f"Не удалось найти бронирование с ID {booking_id}.")


# Определяем команды для каждой роли
commands = {
    "intern": [
        "Бронирование:\n/book",
        "Просмотр/отмена моих бронирований:\n/listbookings",
        "Просмотр пользователя, забронировавшего выбранный компьютер в выбранное время:\n/checkcomputer",
        "Отображение схемы лаборатории:\n/printscheme"
    ],
    "supervisor": [
        "Просмотр/отмена бронирований других пользователей:\n/listbookings `username`",
        "Добавление стажеров:\n/addintern `список tg-имен стажеров через пробел`",
        "Добавление компьютеров:\n/addcomputer `список номеров компьютеров`",
        "Удаление компьютеров:\n/removecomputer `список номеров компьютеров`",
        "Список доступных компьютеров:\n/listcomputers"
    ],
    "administrator": [
        "Добавление руководителей:\n/addsuper `список tg-имен руководителей`",
        "Просмотр списка руководителей:\n/listsupers",
        "Удаление пользователя:\n/deluser `имя пользователя`"
    ]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_privileges(update.message.from_user.username, 'intern'):
        message = "Вы не авторизованы, обратитесь к руководителю для добавления в список пользователей."
    else:
        user_role = get_user_role(update.message.from_user.username)
        # Объединяем команды для текущей роли
        available_commands = []
        for role in commands:
            available_commands.extend(commands[role])
            if role == user_role:
                break
        message = "Список доступных команд:\n" + "\n".join(available_commands)

    await update.message.reply_text(message, parse_mode="MarkdownV2")

async def print_scheme(update: Update, context: CallbackContext):
    if not check_privileges(update.message.from_user.username, 'intern'):
        await update.message.reply_text("Вы не авторизованы, обратитесь к руководителю для добавления в список пользователей.")
        return
    # Путь к изображению на сервере
    image_path = "scheme.jpg"

    # Отправка изображения
    try:
        await update.message.reply_photo(
            photo=open(image_path, 'rb'),  # Открываем файл в режиме чтения байтов
            caption="Схема лаборатории"   # Подпись к изображению (опционально)
        )
    except FileNotFoundError:
        await update.message.reply_text("Изображение не найдено.")
