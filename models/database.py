import psycopg2
from psycopg2 import pool
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'service_bot_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'host': os.getenv('DB_HOST', 'localhost'),  # Если Docker, замените на 'db'
    'port': os.getenv('DB_PORT', '5432')
}

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_CONFIG)
    if db_pool:
        logger.info("Database connection pool created successfully")
    else:
        logger.error("Failed to create database connection pool")
except Exception as e:
    logger.error(f"Error creating database connection pool: {str(e)}")
    raise

def init_db():
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        logger.info("Initializing database schema")
        cursor.execute('''CREATE TABLE IF NOT EXISTS cities (
            id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, telegram_id TEXT UNIQUE NOT NULL, username TEXT, 
            role TEXT NOT NULL, city_id INTEGER REFERENCES cities(id), 
            rating REAL DEFAULT 0, completed_orders INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_categories (
            user_id INTEGER REFERENCES users(id), category_id INTEGER REFERENCES categories(id), 
            PRIMARY KEY (user_id, category_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL, 
            category_id INTEGER REFERENCES categories(id), city_id INTEGER REFERENCES cities(id), 
            price REAL, deadline TEXT, start_date TEXT, status TEXT NOT NULL, 
            customer_id INTEGER REFERENCES users(id), executor_id INTEGER REFERENCES users(id))''')
        cursor.execute("INSERT INTO cities (name) VALUES ('Алматы'), ('Астана'), ('Шымкент') ON CONFLICT DO NOTHING")
        cursor.execute("INSERT INTO categories (name) VALUES ('Сантехника'), ('IT'), ('Уборка') ON CONFLICT DO NOTHING")
        conn.commit()
        logger.info("Database schema initialized successfully")
        db_pool.putconn(conn)
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise