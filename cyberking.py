ADMIN_ID = 7229552057

import telebot
from telebot import types
import time
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ReadTimeout
import sqlite3
import logging


logging.basicConfig(
    level=logging.ERROR,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename = 'bot_errors.log',
    filemode = 'a'
)


bot = telebot.TeleBot('7820681321:AAHqm4A5wbPSTmJfHtur0PSwkMN2I4WgXXM')

welcome_text = """
CyberKing — твой компьютерный клуб в центре Ростова!

На улице Лермонтовская, 57, в самом сердце города, находится место, где сбываются мечты всех геймеров и любителей технологий — CyberKing!

У нас ты найдешь:
🎮 Мощные компьютеры с топовым железом для комфортной игры в любые проекты — от классики до новинок.
💸 Отличные цены — мы заботимся о том, чтобы каждый мог позволить себе качественный отдых.
🌟 Уютная атмосфера — стильный интерьер, удобные кресла и приятная музыка создают идеальное настроение для игр и общения.
👨‍💻 Отзывчивые администраторы — всегда помогут, подскажут и сделают твой визит максимально комфортным.

CyberKing — это не просто компьютерный клуб, это место, где собираются единомышленники, где рождаются новые дружбы и яркие эмоции. Приходи один или с друзьями — скучно не будет!

📍 Адрес: Ростов-на-Дону, ул. Лермонтовская, 57
📞 Звони, чтобы забронировать место: +7 (XXX) XXX-XX-XX

CyberKing — твоя территория игр и впечатлений! Ждем тебя! 🚀
"""

conn = sqlite3.connect('Cyber_King_bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS users')
cursor.execute('DROP TABLE IF EXISTS user_requests')
cursor.execute('DROP TABLE IF EXISTS user_balance')
cursor.execute('DROP TABLE IF EXISTS referrals')
cursor.execute('DROP TABLE IF EXISTS transactions')

conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    phone_number TEXT,
    password TEXT,
    join_date TEXT            
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_requests(
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    request_type TEXT,
    request_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)               
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_balance (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS referrals (
    referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER,
    referral_date TEXT,
    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
    FOREIGN KEY (referred_id) REFERENCES users (user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    transaction_type TEXT,
    amount INTEGER,
    description TEXT,
    transaction_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS tournaments (
    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    date TEXT
)
''')

conn.commit()

def add_transaction(user_id, transaction_type, amount, description):
    try:
        cursor.execute('''
        INSERT INTO transactions (user_id, transaction_type, amount, description, transaction_date)
        VALUES (?, ?, ?, ?, datetime('now'))
        ''', (user_id, transaction_type, amount, description))
        conn.commit
    except Exception as e:
        logging.error(f'Ошибка при добавлении транзакции: {e}')

def add_user(user_id, username, first_name, last_name, referrer_id = None):
    try:
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, join_date)
        VALUES (?, ?, ?, ?, datetime('now'))
        ''', (user_id, username, first_name, last_name))
        conn.commit()

        if referrer_id:
            cursor.execute('''
            INSERT INTO referrals (referrer_id,referred_id, referral_date)
            VALUES (?, ?, datetime('now'))
            ''', (referrer_id, user_id))
            conn.commit()

            update_user_balance(referrer_id, 30)
            add_transaction(referrer_id, 'bonus', 30 * 100, 'Бонус за приглашение')

    except Exception as e:
        logging.error(f'Ошибка при добавлении пользователя: {e}')

def add_user_request(user_id, request_type):
    try:
        cursor.execute('''
        INSERT INTO user_requests (user_id, request_type, request_date)
        VALUES (?,?, datetime('now'))
        ''', (user_id, request_type))
        conn.commit()
    except Exception as e:
        logging.error(f'Ошибка при добавлении запроса пользователя: {e}')

def get_user_balance(user_id):
    try:
        cursor.execute('SELECT balance FROM user_balance WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        logging.error(f'Ошибка при получении баланса: {e}')
        return 0

def update_user_balance(user_id, minutes):
    try:
        cursor.execute('''
        INSERT OR IGNORE INTO user_balance (user_id, balance) VALUES (?,0)
        ''', (user_id,))
        cursor.execute('''
        UPDATE user_balance SET balance = balance + ? WHERE user_id = ?
         ''', (minutes, user_id))
        conn.commit()
    except Exception as e:
        logging.error(f'Ошибка при обновлении баланса: {e}')

def is_user_registered(user_id):
    try:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result is not None 
    except Exception as e:
        logging.error(f'Ошибка при проверке регистрации пользователя {e}')
        return False               

def create_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_price = types.KeyboardButton('💳/price')
    button_prizes = types.KeyboardButton('🎁/prizes')
    button_iron = types.KeyboardButton('🖥/iron')
    button_combo = types.KeyboardButton('🎟/combo')
    button_games = types.KeyboardButton('🎮/games')
    button_tournaments = types.KeyboardButton('🏆/tournaments')
    button_deposit = types.KeyboardButton('💵/deposit_funds')
    button_profile = types.KeyboardButton('🤖/profile')
    button_ref = types.KeyboardButton('👥/ref')
    button_history = types.KeyboardButton('📜/history')
    markup.add(button_price, button_prizes, button_iron, button_combo, button_games, button_tournaments, button_deposit, button_profile, button_ref, button_history)
    return markup

def create_tariff_keyboard():
    markup = types.ReplyKeyboardMarkup (row_width=2, resize_keyboard=True)
    button_50 = types.KeyboardButton ('50 рублей (15 минут)')
    button_100 = types.KeyboardButton ('100 рублей (30 минут)')
    button_custom = types.KeyboardButton ('Ввести свою сумму')
    markup.add(button_50, button_100, button_custom)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        referrer_id = None
        if len(message.text.split()) > 1:
            referrer_id = int(message.text.split()[1])

        add_user(user_id, username, first_name, last_name, referrer_id)

        bot.send_message(message.chat.id, welcome_text, reply_markup=create_reply_keyboard())

    except Exception as e:
        logging.error(f'Ошибка в команде /start: {e}')

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, 'У вас нет доступа к этой команде.')
        return
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_users = types.KeyboardButton('👤 Пользователи')
    button_transactions = types.KeyboardButton('💳 Транзакции')
    button_tournaments = types.KeyboardButton('🏆 Турниры')
    button_broadcast = types.KeyboardButton('📢 Рассылка')
    markup.add(button_users, button_transactions, button_tournaments, button_broadcast)

    bot.send_message(message.chat.id, 'Админ-панель:', reply_markup = markup)

@bot.message_handler(func = lambda message: message.text == '👤 Пользователи' and message.from_user.id == ADMIN_ID)
def view_users(message):
    try:
        cursor.execute('SELECT user_id, username, first_name, last_name, join_date FROM users')
        users = cursor.fetchall()

        if not users:
            bot.send_message(message.chat.id, 'Пользователи не найдены.')
            return
        
        response = "👤 *Список пользователей:*\n\n"
        for user in users:
            user_id, username, first_name, last_name, join_date = user
            response += (
                f"🆔 *ID:* {user_id}\n"
                f"👤 *Имя:* {first_name} {last_name}\n"
                f"📅 *Дата регистрации:* {join_date}\n\n"
            )

        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Ошибка при просмотре пользователей: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при получении списка пользователей.')

@bot.message_handler(func=lambda message: message.text == '💳 Транзакции' and message.from_user.id == ADMIN_ID)
def view_transactions(message):
    try:
        cursor.execute('SELECT * FROM transactions ORDER BY transactions_date DESC')
        transactions = cursor.fetchall()

        if not transactions:
            bot.send_message(message.chat.id, 'Транзакции не найдены')
            return
        
        response = "💳 *Список транзакций:*\n\n"
        for transaction in transactions:
            transaction_id, user_id, transaction_type, amount, description, transaction_date = transaction
            response += (
                f"📅 *Дата:* {transaction_date}\n"
                f"🆔 *Пользователь:* {user_id}\n"
                f"💳 *Тип:* {transaction_type}\n"
                f"💰 *Сумма:* {amount / 100} руб.\n"
                f"📝 *Описание:* {description}\n\n"
            )
            bot.send_message(message.chat.id, response, parse_mode='Markdown')

    except Exception as e:
        logging.error(f'Ошибка при просмотре транзакций: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при получении списка транзакций.')

@bot.message_handler(func=lambda message: message.text == '📜/history')
def handle_history(message):
    try:
        user_id = message.from_user.id
        is_admin = user_id == ADMIN_ID # Проверяем, является ли пользователь администратором

        if is_admin:
            cursor.execute('SELECT * FROM transactions ORDER BY transaction_date DESC')

        else:
            cursor.execute('SELECT * FROM transactions WHERE user_id = ? ORDER BY transaction_date DESC', (user_id,))

            transactions = cursor.fetchall()

            if not transactions:
                bot.send_message(message.chat.id, 'История транзакций пуста.')
                return
            
            response = '📜 *История транзакций:*\n\n'
            for transaction in transactions:
                transaction_id, user_id, transaction_type, amount, description, transaction_date = transaction
                response += (
                    f"📅 *Дата:* {transaction_date}\n"
                f"💳 *Тип:* {transaction_type}\n"
                f"💰 *Сумма:* {amount / 100} руб.\n"
                f"📝 *Описание:* {description}\n\n"
                )
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Ошибка в команде /history {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при получении истории транзакций')

@bot.message_handler(func = lambda message: message.text == '🏆 Турниры' and message.from_user.id == ADMIN_ID)
def add_tournament(message):
    try:
        bot.send_message(message.chat.id, 'Введите название турнира:')
        bot.register_next_step_handler(message, process_tournament_name)
    except Exception as e:
        logging.error(f'Ошибка при добавлении турнира: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при добавлении турнира.')

def process_tournament_name(message):
    try:
        tournament_name = message.text
        bot.send_message(message.chat.id, 'Введите дату турнира (в формате ГГГГ-ММ-ДД):')
        bot.register_next_step_handler(message, process_tournament_date, tournament_name)
    except Exception as e:
        logging.error(f'Ошибка при обработке названия турнира: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при обработке названия турнира.')

def process_tournament_date(message, tournament_name):
    try:
        tournament_date = message.text
        cursor.execute('INSERT INTO tournaments (name, date) VALUES (?, ?)', (tournament_name, tournament_date))
        conn.commit()
        bot.send_message(message.chat.id, f"Турнир '{tournament_name}' успешно добавлен на {tournament_date}.")
    except Exception as e:
        logging.error(f'Ошибка при обработке даты турнира: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при добавлении турнира.')

@bot.message_handler(func = lambda message: message.text == '📢 Рассылка' and message.from_user.id == ADMIN_ID)
def broadcast_message(message):
    try:
        bot.send_message(message.chat.id, 'Введите сообщение для рассылки:')
        bot.register_next_step_handler(message, process_broadcast_message)
    except Exception as e:
        logging.error(f'Ошибка при запуске рассылки: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при запуске рассылки.')

def process_broadcast_message(message):
    try:
        broadcast_text = message.text
        cursor.execute('SELECT user_id From users')
        users = cursor.fetchall()

        for user in users:
            try:
                bot.send_message(user[0], broadcast_text)
            except Exception as e:
                logging.error(f'Ошибка при отправке сообщения пользователя {user[0]}: {e}')

        bot.send_message(message.chat.id, 'Рассылка завершена.')
    except Exception as e:
        logging.error(f'Ошибка при обработке рассылки: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при рассылке сообщений.')

@bot.message_handler(func=lambda message: message.text == '👥/ref')
def handle_ref(message):
    try:
        user_id = message.from_user.id
        ref_link = f'https://t.me/{bot.get_me().username}?start = {user_id}'

        cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?',(user_id,))
        ref_count = cursor.fetchone()[0]

        bot.send_message (
            message.chat.id,
            f"👥 *Ваша реферальная ссылка:*\n"
            f"`{ref_link}`\n\n"
            f"📊 *Приглашено пользователей:* {ref_count}\n"
            f"🎁 *Ваш бонус:* {ref_count * 30} минут",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f'Ошибка в команде /ref {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при обработке запроса')

@bot.message_handler(func=lambda message: message.text == '💵/deposit_funds')
def handle_deposit(message):
    try:
        bot.send_message(message.chat.id, 'Выберите тариф или введите свою сумму', reply_markup=create_tariff_keyboard())
    except Exception as e:
        logging.error(f'Ошибка при отправке счета: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при пополнении баланса. Пожалуйста попробуйте позже.')

@bot.message_handler(func=lambda message: message.text in ['50 рублей (15 минут)', '100 рублей (30 минут)'])
def handle_tariff(message):
    try:
        if message.text == '50 рублей (15 минут)':
            amount = 5000 # 50 рублей в копейках
            minutes = 15
        elif message.text == '100 рублей (30 минут)':
            amount = 10000 # 100 рублей в копейках
            minutes = 30

        #Отправляем счет на оплату
        title = 'Пополнение баланса'
        description = f'Пополнение на {amount / 100} рублей ({minutes} минут)'
        payload = 'unique-payload'
        provider_token = 'YOUR_PROVIDER_TOKEN' # Заменить на свой токен
        start_parameter = 'test'
        currency = 'RUB'
        prices = [types.LabeledPrice(label = f'{amount / 100} рублей', amount=amount)]

        bot.send_invoice(
            message.chat.id,
            title,
            description,
            payload,
            provider_token,
            start_parameter,
            currency,
            prices
        )
    except ValueError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите корректную сумму')

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    try:
        user_id = message.from_user.id
        payment_info = message.successful_payment

        minutes = (payment_info.total_amount // 5000) * 15
        update_user_balance(user_id, minutes)

        bot.send_message(message.chat.id, f'Ваш баланс успешно пополнен на {minutes} минут!')

        admin_message = (
            f'Успешная оплата!\n'
            f'Пользовательно: {message.from_user.username} (ID: {user_id})\n'
            f'Сумма: {payment_info.total_amount / 100} рублей\n'
            f'Зачислено минут: {minutes}'            
        )
        bot.send_message(ADMIN_ID, admin_message)
    except Exception as e:
        logging.error(f'Ошибка при обработке успешного платежа: {e}')
        bot.send_message(message.chat.id, 'Произошла ошибка при обработке платежа ')

@bot.message_handler(commands=['price'])
def send_photo_price(message):
    try:
        user_id = message.from_user.id
        add_user_request(user_id, 'price')

        photos = [
            ('CyberKing/jpg/Цены.jpg')
        ]
        for photo_path in photos:
            try:
                with open(photo_path, 'rb') as file:
                    bot.send_photo(message.chat.id, file)
            except FileNotFoundError:
                logging.error(f'Фотография {photo_path} не найдена.')
                bot.send_message(message.chat.id, f"Фотография {photo_path} не найдена.")
    except Exception as e:
        logging.error(f'Ошибка в команде /price: {e}')

@bot.message_handler(commands=['profile'])
def user_profile(message):
    try:
        user_id = message.from_user.id 
        balance = get_user_balance(user_id)

        text = f"👤 *Ваш профиль:*\n" \
               f"📌 *ID:* {user_id}\n" \
               f"💰 *Баланс:* {balance} минут\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Ошибка в команде /profile: {e}')
        bot.send_message(message.chat.id, 'Ошибка при загрузке профиля')

@bot.message_handler(commands=['prizes'])
def send_photo_prizes(message):
    try:
        user_id = message.from_user.id
        add_user_request(user_id, 'prizes')

        photos = [
            ('CyberKing/jpg/prizes 1.jpg'),
            ('CyberKing/jpg/prizes 2.jpg'),
            ('CyberKing/jpg/prizes 3.jpg')
        ]
        for photo_path in photos:
            try:
                with open(photo_path, 'rb') as file:
                    bot.send_photo(message.chat.id, file)
            except FileNotFoundError:
                logging.error(f'Фотография {photo_path} не найдена.')
                bot.send_message(message.chat.id, f'Фотография {photo_path} не найдена.')
    except Exception as e:
        logging.error(f'Ошибка в команде /prizes: {e}')

@bot.message_handler(commands=['iron'])
def send_photo_iron(message):
    try:
        user_id = message.from_user.id
        add_user_request(user_id, 'iron')

        photos = [
            'CyberKing/jpg/iron.jpg'
        ]
        for photo_path in photos:
            try:
                with open(photo_path, 'rb') as file:
                    bot.send_photo(message.chat.id, file)
            except FileNotFoundError:
                logging.error(f'Фотография {photo_path} не найдена.')
                bot.send_message(message.chat.id, f'Фотография {photo_path} не найдена.')
    except Exception as e:
        logging.error(f'Ошибка в команде /iron: {e}')

@bot.message_handler(commands=['combo'])
def send_photo_combo(message):
    try:
        user_id = message.from_user.id
        add_user_request(user_id, 'combo')

        photos = [
            'CyberKing/jpg/combo.jpg'
        ]
        for photo_path in photos:
            try:
                with open(photo_path, 'rb') as file:
                    bot.send_photo(message.chat.id, file)
            except FileNotFoundError:
                logging.error(f'Фотография {photo_path} не найдена.')
                bot.send_message(message.chat.id, f'Фотография {photo_path} не найдена.')
    except Exception as e:
        logging.error(f'Ошибка в команде /combo: {e}')

@bot.message_handler(commands=["games"])
def send_photo_games(message):
    try:
        user_id = message.from_user.id
        add_user_request(user_id, 'games')

        photos = [
            'CyberKing/jpg/games.jpg'
        ]
        for photo_path in photos:
            try:
                with open(photo_path, 'rb') as file:
                    bot.send_photo(message.chat.id, file)
            except FileNotFoundError:
                logging.error(f'Фотография {photo_path} не найдена.')
                bot.send_message(message.chat.id, f'Фотография {photo_path} не найдена.')
    except Exception as e:
        logging.error(f'Ошибка в команде /games: {e}')

@bot.message_handler(commands=['tournaments'])
def send_photo_tournaments(message):
    try:
        user_id = message.from_user.id
        add_user_request(user_id, 'tournaments')

        photos = [
            'CyberKing/jpg/cup.jpg'
        ]
        for photo_path in photos:
            try:
                with open(photo_path, 'rb') as file:
                    bot.send_photo(message.chat.id, file)
            except FileNotFoundError:
                logging.error(f'Фотография {photo_path} не найдена.')
                bot.send_message(message.chat.id, f'Фотография {photo_path} не найдена.')
    except Exception as e:
        logging.error(f'Ошибка в команде /tournaments: {e}')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == '💳/price':
        send_photo_price(message)
    elif message.text == '🎁/prizes':
        send_photo_prizes(message)
    elif message.text == '🖥/iron':
        send_photo_iron(message)
    elif message.text == '🎟/combo':
        send_photo_combo(message)
    elif message.text == '🎮/games':
        send_photo_games(message)
    elif message.text == '🏆/tournaments':
        send_photo_tournaments(message)
    elif message.text == '💵/deposit_funds':
        handle_deposit(message)
    elif message.text == "🤖/profile":
        user_profile(message)
    else:
        bot.send_message(message.chat.id, 'Я не понимаю эту команду. Попробуйте еще раз.')

while True:
    try:
        bot.polling(timeout = 60)
    except (ReadTimeoutError, ReadTimeout) as e:
        print(f'Ошибка: {e}. Повторная попытка через 10 секунд...')
        time.sleep(10)
    except Exception as e:
        print(f'Критичиская ошибка: {e}. Перезапуск бота...')
        time.sleep(10)
