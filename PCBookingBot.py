from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from frontend import start, addsuper, listsupers, listusers, deluser, addintern, \
                     addcomputer, removecomputer, listcomputers, book, \
                     check_computer, list_bookings, cancel_booking_callback,\
                     handle_date_selection, handle_time_selection, \
                     handle_end_time_selection, handle_computer_selection, \
                     print_scheme
from backend import init_db, init_admin
# import threading
import os
TOKEN = os.getenv("PC_BOOKING_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Токен бота не найден! Установите переменную окружения PC_BOOKING_BOT_TOKEN.")

# Основная функция для запуска бота
def main():
    # Инициализируем базу данных и администратора
    init_db()
    init_admin()
    # threading.Thread(target=delete_expired_bookings, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addsuper", addsuper))
    application.add_handler(CommandHandler("listsupers", listsupers))
    application.add_handler(CommandHandler("listusers", listusers))
    application.add_handler(CommandHandler("deluser", deluser))
    application.add_handler(CommandHandler("addintern", addintern))
    application.add_handler(CommandHandler("addcomputer", addcomputer))
    application.add_handler(CommandHandler("removecomputer", removecomputer))
    application.add_handler(CommandHandler("listcomputers", listcomputers))
    application.add_handler(CommandHandler("book", book))
    application.add_handler(CommandHandler("checkcomputer", check_computer))
    application.add_handler(CallbackQueryHandler(handle_date_selection, pattern=r'^book \d{4}-\d{2}-\d{2}$'))
    application.add_handler(CallbackQueryHandler(handle_time_selection, pattern=r'^check \d{4}-\d{2}-\d{2}$'))
    application.add_handler(CallbackQueryHandler(handle_time_selection, pattern=r'^book \d{4}-\d{2}-\d{2} \d+$'))
    application.add_handler(CallbackQueryHandler(handle_end_time_selection, pattern=r'^check \d{4}-\d{2}-\d{2} \d+$'))
    application.add_handler(CallbackQueryHandler(handle_end_time_selection, pattern=r'^book \d{4}-\d{2}-\d{2} \d+ \d+$'))
    application.add_handler(CallbackQueryHandler(handle_computer_selection, pattern=r'^\d+ \d+ \d+ \d+$'))
    # Регистрация одной команды для просмотра бронирований
    application.add_handler(CommandHandler('listbookings', list_bookings))
    # Регистрация хэндлера для обработки отмены бронирований через кнопки
    application.add_handler(CallbackQueryHandler(cancel_booking_callback, pattern=r'^cancel_\d+$'))
    # Регистрация команды вывода схемы компьютеров в лабе
    application.add_handler(CommandHandler('printscheme', print_scheme))

    # Запуск бота
    print("Starting bot...")
    application.run_polling(poll_interval=1, timeout=10)  # Запуск бота

if __name__ == '__main__':
    main()
