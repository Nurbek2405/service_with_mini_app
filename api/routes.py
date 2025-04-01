from flask import send_from_directory, request, jsonify, redirect, url_for
from models.entities import User, Order
from models.database import db_pool
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_api(app, telegram_app):
    app.db_pool = db_pool

    @app.route('/')
    def serve_index():
        return redirect(url_for('serve_miniapp'))

    @app.route('/miniapp')
    def serve_miniapp():
        return send_from_directory('static', 'miniapp.html')

    @app.route('/register', methods=['POST'])
    def register():
        try:
            data = request.json
            telegram_id = data['telegram_id']
            username = data['username']
            role = data['role']
            city_id = int(data['city_id'])
            category_ids = [int(cat_id) for cat_id in data.get('category_ids', [])]
            logger.info(f"Registering user: telegram_id={telegram_id}, role={role}, city_id={city_id}, categories={category_ids}")

            user_id = User.create(telegram_id, username, role, city_id)
            for cat_id in category_ids:
                User.add_category(user_id, cat_id)
            logger.info(f"User registered successfully: user_id={user_id}")
            return jsonify({"message": "Регистрация завершена", "user_id": user_id}), 200
        except KeyError as e:
            logger.error(f"Missing field: {str(e)}")
            return jsonify({"error": f"Отсутствует поле: {str(e)}"}), 400
        except psycopg2.Error as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": f"Ошибка базы данных: {str(e)}"}), 500
        except ValueError as e:
            logger.error(f"Invalid data format: {str(e)}")
            return jsonify({"error": "Неверный формат данных"}), 400
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({"error": f"Неизвестная ошибка: {str(e)}"}), 500

    @app.route('/create_order', methods=['POST'])
    def create_order():
        try:
            data = request.json
            order_id = Order.create(
                data['title'], data['description'], int(data['category_id']),
                int(data['city_id']), data['start_date'], data['deadline'], data['customer_id']
            )
            logger.info(f"Order created: order_id={order_id}")
            return jsonify({"order_id": order_id}), 200
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/update_profile', methods=['POST'])
    def update_profile():
        try:
            data = request.json
            telegram_id = data['telegram_id']
            city_id = int(data['city_id'])
            category_ids = [int(cat_id) for cat_id in data.get('category_ids', [])]
            User.update_profile(telegram_id, city_id, category_ids)
            logger.info(f"Profile updated for telegram_id={telegram_id}")
            return jsonify({"message": "Профиль обновлён"}), 200
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/get_profile', methods=['POST'])
    def get_profile():
        try:
            data = request.json
            telegram_id = data['telegram_id']
            profile = User.get_profile(telegram_id)
            if profile:
                logger.info(f"Profile retrieved for telegram_id={telegram_id}")
                return jsonify(profile), 200
            logger.warning(f"User not found: telegram_id={telegram_id}")
            return jsonify({"error": "Пользователь не найден"}), 404
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return jsonify({"error": str(e)}), 500