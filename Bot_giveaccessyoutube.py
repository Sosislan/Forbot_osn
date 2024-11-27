import telebot
import sqlite3 as sq
from config import Giveaccessyoutube  # Імпорт API ключа з config.py

bot = telebot.TeleBot(Giveaccessyoutube)

# Створюємо клавіатуру
markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
invite_button = telebot.types.KeyboardButton('Запросити користувача')
send_sms_button = telebot.types.KeyboardButton('Користувачі без доступу')
send_info_button = telebot.types.KeyboardButton('Інформація') # Нова кнопка
markup.add(invite_button, send_sms_button, send_info_button)

markup_admin = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
send_info_button_admin = telebot.types.KeyboardButton('Інформація') # Нова кнопка
markup_admin.add(send_info_button_admin, send_sms_button)

my_id = 6673121916

# Підключення до бази даних та створення таблиці
with sq.connect("Chanelsyoutube_base.db") as con:
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            num_newchanel INTEGER DEFAULT 0,
            num_buy INTEGER DEFAULT 0,
            last_channel_index INTEGER DEFAULT 0
        )
    """)

# Пропускаємо старі оновлення
def skip_old_updates():
    updates = bot.get_updates(timeout=1)
    if updates:
        # Беремо ID останнього оновлення
        return updates[-1].update_id + 1
    return None

# Отримуємо останній update_id
last_update_id = skip_old_updates()

# Створюємо словник для збереження стану перевірки пароля
user_states = {}

# Функція для перевірки та оновлення статусу користувача
def update_user_access(username, message):
    username = username.lstrip('@')  # Видаляємо @, якщо він є
    with sq.connect("Chanelsyoutube_base.db") as con:
        cur = con.cursor()
        cur.execute("SELECT id, num_buy FROM users WHERE username = ?", (username,))
        user_data = cur.fetchone()

        if user_data:
            user_id, num_buy = user_data
            if num_buy == 0:
                # Оновлюємо num_buy на 1
                cur.execute("UPDATE users SET num_buy = 1 WHERE id = ?", (user_id,))
                con.commit()
                bot.send_message(
                    message.chat.id,
                    f"Користувач @{username} успішно отримав доступ до каналів!"
                )
            else:
                bot.send_message(
                    message.chat.id,
                    f"Користувач @{username} уже має доступ до каналів."
                )
        else:
            bot.send_message(
                message.chat.id,
                f"Користувача @{username} не знайдено в базі. Перевірте правильність введення."
            )
        return
# Функція для надсилання повідомлень користувачам без доступу
def send_message_to_users_without_access(message):
    with sq.connect("Chanelsyoutube_base.db") as con:
        cur = con.cursor()
        cur.execute("SELECT username, id FROM users WHERE num_buy = 0")  # Вибираємо користувачів без доступу
        users = cur.fetchall()

        if users:
            for user in users:
                bot.send_message(
                    message.chat.id,
                    f"Користувач який не купив бота @{user[0]}")
        else:
            bot.send_message(message.chat.id, "Немає користувачів без доступу.")

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привіт!"
    )
    bot.send_message(message.chat.id, "Введіть пароль для доступу:")
    user_states[message.chat.id] = 'awaiting_password'

# Обробка кнопки
@bot.message_handler(content_types=['text'])
def main(message):
    user_id = message.chat.id

    # Перевірка стану користувача
    if user_states.get(user_id) == 'awaiting_password':
        if message.text == '28072006':  # Правильний пароль
            user_states[user_id] = 'authenticated'
            bot.send_message(user_id, "Доступ надано.", reply_markup=markup)
        elif message.text == '28072006-admin':  # Правильний пароль
            if message.from_user.username == 'cashplag':
                user_states[user_id] = 'authenticated_admin'
                bot.send_message(user_id, "Доступ надано.", reply_markup=markup_admin)
            else:
                bot.send_message(user_id, "Ви хто?", reply_markup=markup_admin)
        else:
            pass
        return
    if user_states.get(user_id) == 'authenticated':
        if message.text == 'Запросити користувача':
            bot.send_message(user_id, "Введіть @username користувача.")
        elif message.text.startswith('@'):  # Якщо введено username
            update_user_access(message.text, message)
        elif message.text == 'Інформація' or message.text == 'Інфо':
            num = 0
            num_buy = 0
            maks = 0
            with sq.connect("Chanelsyoutube_base.db") as con:
                cur = con.cursor()
                cur.execute("SELECT username, num_newchanel, num_buy FROM users")
                for user in cur.fetchall():
                    num += 1
                    if user[2] == '1' or user[2] == 1:
                        num_buy += 1
                    if user[1] == '':
                        maks = 0
                    else:
                        if maks < user[1]:
                            maks = user[1]
                    if message.text != 'Інфо':
                        bot.send_message(user_id,
                                        f"Ім'я: {user[0]}, Кількість пройдених каналів: {user[1]}, статус покупки = {user[2]}")
            bot.send_message(user_id, f"Всього користувачі - {num}\n"
                                      f"Користувачів з доступом - {num_buy}\n"
                                      f"Користувачів без доступу - {num - num_buy}\n"
                                      f"Найбільша кількість пройдених каналів - {maks}")
        elif message.text == 'Користувачі без доступу':
            send_message_to_users_without_access(message)
        else:
            bot.send_message(user_id, "Я вас не зрозумів або введіть @username користувача.")
    elif user_states.get(user_id) == 'authenticated_admin':
        if message.text == 'Інформація':
            with sq.connect("Chanelsyoutube_base.db") as con:
                cur = con.cursor()
                cur.execute("SELECT username, last_channel_index, num_buy FROM users")
                for user in cur.fetchall():
                    bot.send_message(user_id, f"Ім'я: {user[0]}, Кількість пройдених каналів: {user[1]}, статус покупки = {user[2]}")
        elif message.text.startswith('@'):  # Якщо введено username
            bot.send_message(my_id, f"Введено користувача {message.text}")
            update_user_access(message.text, message)
        elif message.text == 'Користувачі без доступу':
            send_message_to_users_without_access(message)
        else:
            bot.send_message(user_id, "Я вас не зрозумів.")
    else:
        bot.send_message(user_id, "Ви не зареєстровані, нажміть на /start")

# Запуск бота
res = True
while res:
    try:
        bot.polling(skip_pending=True, none_stop=True)
        res = False
    except Exception as e:
        print(f"bot_stop: {e}")
        res = True

