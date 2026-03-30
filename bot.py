import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler

# Загрузка переменных из .env
load_dotenv()

# Получение переменных окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
MAYOR_ID = os.getenv("MAYOR_ID")

# Проверка, что переменные заданы
if not TOKEN or not MAYOR_ID:
    raise ValueError("TELEGRAM_TOKEN и MAYOR_ID должны быть указаны в .env файле")

MAYOR_ID = int(MAYOR_ID)  # Преобразуем в int

# Состояние для ConversationHandler
WAITING_TIME = 1

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context) -> int:
    """Начало диалога: запрос времени."""
    await update.message.reply_text("На какое время его зарегистрировать к мэру?")
    return WAITING_TIME

async def receive_time(update: Update, context) -> int:
    """Получение времени и пересылка мэру."""
    user_message = update.message.text
    user_id = update.effective_user.id

    # Отправляем мэру
    await context.bot.send_message(
        chat_id=MAYOR_ID,
        text=f"Пользователь {user_id} хочет записаться на время: {user_message}"
    )
    # Подтверждение пользователю
    await update.message.reply_text("Ваше время передано мэру.")
    return ConversationHandler.END

async def cancel(update: Update, context) -> int:
    """Отмена диалога."""
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main() -> None:
    """Запуск бота."""
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