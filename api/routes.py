from flask import send_from_directory, request, jsonify
from models.entities import User, Order
from app import application
from models.database import db_pool


def init_api(app):
    app.db_pool = db_pool  # Передаём пул соединений в приложение

    @app.route('/')
    def serve_index():
        return send_from_directory('static', 'index.html')

    @app.route('/miniapp')
    def serve_miniapp():
        return send_from_directory('static', 'miniapp.html')

    @app.route('/register', methods=['POST'])
    async def register():
        data = request.json
        telegram_id = data['telegram_id']
        username = data['username']
        role = data['role']
        city_id = data['city_id']
        category_ids = data.get('category_ids', [])

        user_id = User.create(telegram_id, username, role, city_id)
        for cat_id in category_ids:
            User.add_category(user_id, cat_id)
        return jsonify({"message": "Регистрация завершена", "user_id": user_id})

    @app.route('/create_order', methods=['POST'])
    async def create_order():
        data = request.json
        order_id = await Order.create(data['title'], data['description'], data['category_id'],
                                      data['city_id'], data['start_date'], data['deadline'],
                                      data['customer_id'])
        conn = app.db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT telegram_id FROM users u JOIN user_categories uc ON u.id = uc.user_id WHERE uc.category_id = %s AND u.city_id = %s AND u.role = 'Исполнитель'",
            (data['category_id'], data['city_id']))
        executors = cursor.fetchall()
        db_pool.putconn(conn)
        for executor in executors:
            await application.bot.send_message(chat_id=executor[0], text=f"Новый заказ #{order_id}: {data['title']}")
        return jsonify({"order_id": order_id})

    @app.route('/update_profile', methods=['POST'])
    async def update_profile():
        data = request.json
        telegram_id = data['telegram_id']
        city_id = data['city_id']
        category_ids = data.get('category_ids', [])
        User.update_profile(telegram_id, city_id, category_ids)
        return jsonify({"message": "Профиль обновлён"})