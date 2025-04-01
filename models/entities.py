from models.database import db_pool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class User:
    @staticmethod
    def create(telegram_id, username, role, city_id):
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (telegram_id, username, role, city_id) VALUES (%s, %s, %s, %s) RETURNING id",
                           (telegram_id, username, role, city_id))
            user_id = cursor.fetchone()[0]
            conn.commit()
            db_pool.putconn(conn)
            logger.info(f"User created: telegram_id={telegram_id}, user_id={user_id}")
            return user_id
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    def add_category(user_id, category_id):
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user_categories (user_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                           (user_id, category_id))
            conn.commit()
            db_pool.putconn(conn)
            logger.info(f"Category {category_id} added to user {user_id}")
        except Exception as e:
            logger.error(f"Error adding category: {str(e)}")
            raise

    @staticmethod
    def update_profile(telegram_id, city_id, category_ids):
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET city_id = %s WHERE telegram_id = %s", (city_id, telegram_id))
            cursor.execute("DELETE FROM user_categories WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)", (telegram_id,))
            cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
            user_id = cursor.fetchone()[0]
            for cat_id in category_ids:
                cursor.execute("INSERT INTO user_categories (user_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                               (user_id, cat_id))
            conn.commit()
            db_pool.putconn(conn)
            logger.info(f"Profile updated for telegram_id={telegram_id}")
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            raise

    @staticmethod
    def get_profile(telegram_id):
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT id, role, city_id FROM users WHERE telegram_id = %s", (telegram_id,))
            user = cursor.fetchone()
            if not user:
                db_pool.putconn(conn)
                return None
            user_id, role, city_id = user
            cursor.execute("SELECT category_id FROM user_categories WHERE user_id = %s", (user_id,))
            category_ids = [row[0] for row in cursor.fetchall()]
            db_pool.putconn(conn)
            return {"user_id": user_id, "role": role, "city_id": city_id, "category_ids": category_ids}
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            raise

class Order:
    @staticmethod
    def create(title, description, category_id, city_id, start_date, deadline, customer_id):
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO orders (title, description, category_id, city_id, start_date, deadline, status, customer_id)
                              VALUES (%s, %s, %s, %s, %s, %s, 'Открыт', %s) RETURNING id''',
                           (title, description, category_id, city_id, start_date, deadline, customer_id))
            order_id = cursor.fetchone()[0]
            conn.commit()
            db_pool.putconn(conn)
            logger.info(f"Order created: order_id={order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise