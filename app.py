import psycopg2
from psycopg2 import pool
from flask import Flask, request, jsonify, send_from_directory
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, ContextTypes
from telegram.ext import filters  # Фильтры для обработки сообщений
import asyncio
import os

# Настройки Flask
app = Flask(__name__, static_folder='static')

# Настройки Telegram Bot
TOKEN = '7661263528:AAHB4LKirWI6Xtw_MRIgrzQPqq22Xz-_AUI'  # Замените на токен от @BotFather
application = Application.builder().token(TOKEN).build()

# Настройки PostgreSQL из переменных окружения
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'service_bot_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),  # Замените на ваш пароль
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Пул соединений для PostgreSQL
db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_CONFIG)

# Состояния для регистрации
ROLE, CITY, CATEGORY = range(3)


# Инициализация базы данных
def init_db():
    conn = db_pool.getconn()
    cursor = conn.cursor()

    # Создание таблиц
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            city INTEGER REFERENCES cities(id),
            category INTEGER REFERENCES categories(id),
            rating REAL DEFAULT 0,
            completed_orders INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            description TEXT NOT NULL,
            category INTEGER REFERENCES categories(id),
            city INTEGER REFERENCES cities(id),
            price REAL NOT NULL,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL,
            customer_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Заполнение начальными данными
    cursor.execute("INSERT INTO cities (name) VALUES ('Алматы'), ('Астана'), ('Шымкент') ON CONFLICT DO NOTHING")
    cursor.execute("INSERT INTO categories (name) VALUES ('Сантехника'), ('IT'), ('Уборка') ON CONFLICT DO NOTHING")

    conn.commit()
    db_pool.putconn(conn)


# Flask маршруты
@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')


@app.route('/create_order', methods=['POST'])
async def create_order():
    data = request.json
    telegram_id = data.get('telegram_id')

    conn = db_pool.getconn()
    cursor = conn.cursor()

    # Проверка пользователя
    cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    if not user:
        db_pool.putconn(conn)
        return jsonify({"error": "Пользователь не зарегистрирован"}), 403

    customer_id = user[0]
    cursor.execute('''
        INSERT INTO orders (description, category, city, price, deadline, status, customer_id)
        VALUES (%s, %s, %s, %s, %s, 'открыт', %s)
        RETURNING id
    ''', (data['description'], data['category'], data['city'], data['price'], data['deadline'], customer_id))

    order_id = cursor.fetchone()[0]
    conn.commit()

    # Уведомление исполнителям
    cursor.execute("SELECT telegram_id FROM users WHERE role = 'Исполнитель' AND category = %s AND city = %s",
                   (data['category'], data['city']))
    executors = cursor.fetchmany()
    db_pool.putconn(conn)

    for executor in executors:
        await application.bot.send_message(chat_id=executor[0],
                                           text=f"Новый заказ #{order_id}: {data['description']}\nЦена: {data['price']} тг\nСрок: {data['deadline']}")

    return jsonify({"order_id": order_id})


# Telegram Bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Добро пожаловать! Выберите роль: Заказчик или Исполнитель")
    return ROLE


async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    role = update.message.text
    if role not in ["Заказчик", "Исполнитель"]:
        await update.message.reply_text("Пожалуйста, выберите: Заказчик или Исполнитель")
        return ROLE
    context.user_data['role'] = role

    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM cities")
    cities = cursor.fetchall()
    db_pool.putconn(conn)

    city_list = "\n".join([f"{c[0]}. {c[1]}" for c in cities])
    await update.message.reply_text(f"Выберите город (введите номер):\n{city_list}")
    return CITY


async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        city_id = int(update.message.text)
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cities WHERE id = %s", (city_id,))
        if not cursor.fetchone():
            await update.message.reply_text("Неверный номер города, попробуйте снова")
            db_pool.putconn(conn)
            return CITY
        context.user_data['city'] = city_id
        db_pool.putconn(conn)

        if context.user_data['role'] == "Исполнитель":
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories")
            categories = cursor.fetchall()
            db_pool.putconn(conn)

            category_list = "\n".join([f"{c[0]}. {c[1]}" for c in categories])
            await update.message.reply_text(f"Выберите категорию (введите номер):\n{category_list}")
            return CATEGORY
        else:
            return await save_user(update, context)
    except ValueError:
        await update.message.reply_text("Введите номер города")
        return CITY


async def set_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        category_id = int(update.message.text)
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            await update.message.reply_text("Неверный номер категории, попробуйте снова")
            db_pool.putconn(conn)
            return CATEGORY
        context.user_data['category'] = category_id
        db_pool.putconn(conn)
        return await save_user(update, context)
    except ValueError:
        await update.message.reply_text("Введите номер категории")
        return CATEGORY


async def save_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = db_pool.getconn()
    cursor = conn.cursor()

    telegram_id = str(update.message.from_user.id)
    name = update.message.from_user.first_name
    role = context.user_data['role']
    city = context.user_data['city']
    category = context.user_data.get('category', None)

    cursor.execute('''
        INSERT INTO users (telegram_id, name, role, city, category, rating, completed_orders)
        VALUES (%s, %s, %s, %s, %s, 0, 0)
        ON CONFLICT (telegram_id) DO UPDATE
        SET name = %s, role = %s, city = %s, category = %s, rating = 0, completed_orders = 0
    ''', (telegram_id, name, role, city, category, name, role, city, category))

    conn.commit()
    db_pool.putconn(conn)

    await update.message.reply_text(f"Регистрация завершена!\nРоль: {role}\nГород: {city}")
    return ConversationHandler.END


# Настройка бота
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_role)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_city)],
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_category)],
    },
    fallbacks=[]
)

application.add_handler(conv_handler)

# Запуск
if __name__ == '__main__':
    init_db()

    # Запуск бота в отдельном потоке
    loop = asyncio.get_event_loop()
    loop.create_task(application.run_polling())

    # Запуск Flask
    app.run(debug=True, port=5000)