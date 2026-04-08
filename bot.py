import logging
import os
import json
from datetime import date
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
MAYOR_ID = os.getenv("MAYOR_ID")

if not TOKEN or not MAYOR_ID:
    raise ValueError("TELEGRAM_TOKEN и MAYOR_ID должны быть указаны в переменных окружения")

MAYOR_ID = int(MAYOR_ID)
WAITING_TIME = 1

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файл для хранения записей
APPOINTMENTS_FILE = "appointments.json"

def load_appointments():
    """Загружает записи из JSON файла."""
    if os.path.exists(APPOINTMENTS_FILE):
        with open(APPOINTMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_appointments(appointments):
    """Сохраняет записи в JSON файл."""
    with open(APPOINTMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(appointments, f, ensure_ascii=False, indent=2)

def has_appointment_today(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя запись на сегодня."""
    appointments = load_appointments()
    today_str = date.today().isoformat()
    return str(user_id) in appointments and appointments[str(user_id)] == today_str

def save_appointment_today(user_id: int):
    """Сохраняет запись пользователя на сегодня."""
    appointments = load_appointments()
    appointments[str(user_id)] = date.today().isoformat()
    save_appointments(appointments)

async def start(update: Update, context) -> int:
    """Начало диалога: запрос времени."""
    user_id = update.effective_user.id
    if has_appointment_today(user_id):
        await update.message.reply_text(
            "❌ Вы уже записаны на сегодня.\n"
            "Пожалуйста, попробуйте завтра."
        )
        return ConversationHandler.END
    await update.message.reply_text("На какое время его зарегистрировать к мэру?")
    return WAITING_TIME

async def receive_time(update: Update, context) -> int:
    """Получение времени и пересылка мэру (с проверкой на повтор)."""
    user_id = update.effective_user.id
    user_message = update.message.text

    # Повторная проверка (на случай, если пользователь медлил)
    if has_appointment_today(user_id):
        await update.message.reply_text(
            "❌ Вы уже записаны на сегодня.\n"
            "Дополнительная запись невозможна."
        )
        return ConversationHandler.END

    # Сохраняем запись
    save_appointment_today(user_id)

    # Отправляем мэру
    await context.bot.send_message(
        chat_id=MAYOR_ID,
        text=f"✅ Пользователь {user_id} записался на время: {user_message}"
    )
    await update.message.reply_text(
        "✅ Ваше время передано мэру.\n"
        "Вы можете записаться снова завтра."
    )
    return ConversationHandler.END

async def cancel(update: Update, context) -> int:
    """Отмена диалога."""
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()