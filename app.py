import asyncio
from threading import Thread
from flask import Flask
from telegram.ext import Application
from bot.handlers import setup_handlers
from api.routes import init_api
from models.database import init_db
from config import TOKEN, MINI_APP_URL

app = Flask(__name__, static_folder='static')
application = Application.builder().token(TOKEN).build()

init_db()
setup_handlers(application)
init_api(app, application)  # Передаем application как аргумент

def run_flask():
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    asyncio.run(application.run_polling())