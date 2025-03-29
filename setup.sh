#!/bin/bash


set -e # Остановить скрипт при возникновении ошибки

SCRIPT_DIR="$(dirname "$(realpath "$0")")"

sudo echo "Для работы скрипта нужны права суперпользователя"
echo "Введите токен бота"
read TOKEN
echo "Введите tg-ник пользователя, который станет администратором бота"
read ADMIN_NAME
echo "Введите путь к базе данных бота"
read DB_FILE
python3 -m venv venv
source venv/bin/activate
pip install python-telegram-bot pytz --upgrade

cat <<EOF | sudo tee /etc/systemd/system/pc_booking_bot.service
[Unit]
Description=PC Booking Bot Service
After=network.target

[Service]
# Путь к вашему виртуальному окружению и файлу бота
WorkingDirectory=$SCRIPT_DIR
Environment="PC_BOOKING_BOT_TOKEN=$TOKEN"
Environment="PC_BOOKING_BOT_ADMIN=$ADMIN_NAME"
Environment="PC_BOOKING_BOT_DB=$DB_FILE"
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/PCBookingBot.py

# Настройки пользователя и группы (опционально)
User=$USER
Group=$USER

# Опции перезапуска
Restart=always
RestartSec=5s
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pc_booking_bot.service
sudo systemctl start pc_booking_bot.service