# service_with_mini_app
Телеграм сервис для поиска заказчиков и исполнителей (Перезагрузка)

# Service Bot
Telegram Mini App для заказа услуг в Казахстане с использованием PostgreSQL.

## Установка
1. Установите Python 3.9+.
2. Установите PostgreSQL и создайте базу данных:
   - `createdb service_bot_db`
   - Настройте пользователя и пароль в `app.py` (DB_CONFIG).
3. Установите зависимости: `pip install -r requirements.txt`.
4. Замените `YOUR_TELEGRAM_BOT_TOKEN` в `app.py` на токен от @BotFather.
5. Запустите: `python app.py`.

## Функционал
- Регистрация пользователей через бота (/start).
- Создание заказов через Mini App.
- Уведомления исполнителям о новых заказах.

## Структура
- `app.py`: Flask сервер + Telegram Bot.
- `static/`: Файлы Mini App.
- PostgreSQL: база данных `service_bot_db`.

## Настройка PostgreSQL
1. Установите PostgreSQL (https://www.postgresql.org/download/).
2. Создайте базу: `createdb service_bot_db`.
3. Обновите `DB_CONFIG` в `app.py` с вашими данными (user, password, host, port).