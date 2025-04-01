from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, ContextTypes, filters
from models.entities import User
from config import MINI_APP_URL  # Импорт из config

ROLE, CITY, CATEGORY = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton("Регистрация и профиль в Mini App", web_app={"url": MINI_APP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Зарегистрируйтесь или управляйте профилем через Mini App:", reply_markup=reply_markup)
    return ROLE

async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    role = update.message.text
    if role not in ["Заказчик", "Исполнитель"]:
        await update.message.reply_text("Выберите: Заказчик или Исполнитель")
        return ROLE
    context.user_data['role'] = role
    await update.message.reply_text("Регистрация продолжится в Mini App.")
    return ConversationHandler.END

def setup_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_role)],
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)