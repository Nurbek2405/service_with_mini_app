from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from models.entities import User, City, Category

ADMIN_ID = "YOUR_TELEGRAM_ID"  # Замените на ваш Telegram ID

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != ADMIN_ID:
        await update.message.reply_text("Доступ запрещён.")
        return
    await update.message.reply_text("Админ-панель: /add_city, /del_city, /add_category, /del_category, /del_user")

async def add_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != ADMIN_ID:
        return
    city_name = " ".join(context.args)
    City.create(city_name)
    await update.message.reply_text(f"Город {city_name} добавлен.")

# Другие админ-команды аналогично...

def setup_admin_handlers(application):
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("add_city", add_city))
    # Добавьте остальные команды: del_city, add_category, etc.