import asyncio
from threading import Thread
from flask import Flask
from telegram.ext import Application
from bot.handlers import setup_handlers
from api.routes import init_api
from models.database import init_db

# Настройки Flask
app = Flask(__name__, static_folder='static')

# Настройки Telegram Bot
TOKEN = os.getenv('TELEGRAM_TOKEN', '7661263528:AAHB4LKirWI6Xtw_MRIgrzQPqq22Xz-_AUI')
MINI_APP_URL = "https://fa66-88-204-232-102.ngrok-free.app/miniapp"  # Ваш ngrok-адрес
application = Application.builder().token(TOKEN).build()

# Инициализация
init_db()  # Инициализация базы данных
setup_handlers(application)  # Настройка обработчиков бота
init_api(app)  # Настройка API Flask

# Запуск Flask в отдельном потоке
def run_flask():
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    asyncio.run(application.run_polling())