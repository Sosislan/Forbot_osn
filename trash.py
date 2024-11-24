import telebot
import datetime
import time
import random  # Для генерації випадкових текстів
import sqlite3 as sq
from config import Bot_token_searchyoutube  # Импорт API ключей из config.py

bot = telebot.TeleBot(Bot_token_searchyoutube)

markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
New_chanel = telebot.types.KeyboardButton('Нова підбірка каналів')
Ref_chanel = telebot.types.KeyboardButton('Реферальна програма')
markup.add(New_chanel, Ref_chanel)

# Список шаблонів повідомлень
channel_messages = [
    '''
Привет!
Я заметил твой YouTube-канал "{channel_name}", и он, кажется, давно не обновлялся. Возможно, это то, что тебе интересно обсудить.
Я готов предложить отличные условия для его приобретения. Если это тебя заинтересует, напиши!
''',
    '''
Здравствуйте!
Я нашел ваш YouTube-канал "{channel_name}", и мне показалось, что он уже давно неактивен. Есть идея, как его можно возродить.
Если это для вас актуально, я готов сделать привлекательное предложение!
''',
    '''
Привет!
Твой канал "{channel_name}" привлек мое внимание, хотя кажется, что он давно не обновлялся. У меня есть предложение, которое может быть тебе интересно.
Если тебе это подходит, свяжись со мной, и обсудим!
''',
    '''
Здравствуйте!
Ваш канал "{channel_name}" давно не обновлялся. Я заинтересован в его приобретении.
Если готовы обсудить детали, напишите мне. Это может быть выгодно для нас обоих!
''',
    '''
Привет!
Наткнулся на твой канал "{channel_name}". Похоже, что он в состоянии покоя.
У меня есть идея по его восстановлению и готов предложить хорошую цену. Напиши, если заинтересован!
'''
]

# Пропускаємо старі оновлення
def skip_old_updates():
    updates = bot.get_updates(timeout=1)
    if updates:
        # Беремо ID останнього оновлення
        return updates[-1].update_id + 1
    return None

# Отримуємо останній update_id
last_update_id = skip_old_updates()

# Функція для вибору випадкового повідомлення
def get_random_channel_message(channel_name):
    return random.choice(channel_messages).format(channel_name=channel_name)


# Подключение к базе данных и создание таблицы, если она не существует
with sq.connect("Chanelsyoutube_base.db") as con:
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            num_newchanel INTEGER DEFAULT 0,
            num_buy INTEGER DEFAULT 0,
            last_channel_index INTEGER DEFAULT 0  -- Нове поле для збереження індексу
        )
    """)



# Функция для добавления пользователя в базу данных, если его еще нет
def add_user_to_db(user_id, username, mes):
    with sq.connect("Chanelsyoutube_base.db") as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if cur.fetchone() is None:  # Если пользователя нет в базе
            cur.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
            print(f"Пользователь добавлен в базу данных: {user_id} с username {username}")
            bot.send_message(mes, 'Привіт 🌝🤚.', reply_markup=markup)
        else:
            bot.send_message(mes, 'Ми з тобою вже знайомі!', reply_markup=markup)


# Функция для проверки регистрации пользователя
def is_user_registered(user_id):
    with sq.connect("Chanelsyoutube_base.db") as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        return cur.fetchone() is not None  # Возвращает True, если пользователь существует

@bot.message_handler(commands=['start'])
def Start(message):
    add_user_to_db(message.from_user.id, message.from_user.username, message.chat.id)  # Записуємо username
    bot.send_message(message.from_user.id, "Удачних пошуків сищик)", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def main(message):
    time.sleep(1)  # Затримка в 1 секунду

    if not is_user_registered(message.from_user.id):
        bot.send_message(message.chat.id, "Ви не зареєстровані! Будь ласка, введіть команду /start для реєстрації.")
        return

    with sq.connect("Chanelsyoutube_base.db") as con:
        cur = con.cursor()
        # Отримуємо значення num_buy для користувача
        cur.execute("SELECT num_buy FROM users WHERE id = ?", (message.from_user.id,))
        num_buy = cur.fetchone()[0]

    if num_buy == 0:
        if message.text == 'Реферальна програма':
            bot.send_message(message.chat.id, '''
Не забувай про реферальну систему бота: за кожну людину, яку ти приведеш і яка купить наш бот, 
ти отримаєш 25% від ціни, але якщо користувач придбав дорожче, ваш бонус — 30%.
Тож якщо не вийде з YouTube-каналами, у тебе є шанс заробити безпосередньо з нами та нашою командою!
За деталями звертайтесь: @cashplag
                ''', reply_markup=markup)
            return
        elif message.text == 'Нова підбірка каналів':
            bot.send_message(
                message.chat.id,
                "У вас немає доступу до каналів. Будь ласка, придбайте доступ, щоб продовжити. Придбати можна у @cashplag",
                reply_markup=markup
            )
        else:
            bot.send_message(message.chat.id, f'Я не зрозумів = {message.text}', reply_markup=markup)
        return  # Блокуємо подальші дії

    # Якщо num_buy = 1, перевіряємо текст повідомлення
    if message.text == 'Нова підбірка каналів':
        bot.send_message(message.chat.id, 'Щасти!', reply_markup=markup)
        print(f"Користувач отримує канал: {message.from_user.id} з username {message.from_user.username}")
        process_channels(message)  # Викликаємо функцію обробки каналів
    elif message.text == 'Реферальна програма':
        bot.send_message(message.chat.id, '''
Не забувай про реферальну систему бота: за кожну людину, яку ти приведеш і яка купить наш бот, 
ти отримаєш 25% від ціни, але якщо користувач придбав дорожче, ваш бонус — 30%.
Тож якщо не вийде з YouTube-каналами, у тебе є шанс заробити безпосередньо з нами та нашою командою!
За деталями звертайтесь: @cashplag
        ''', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f'Я не зрозумів = {message.text}', reply_markup=markup)


channels_file = 'inactive_channels.txt'
processed_channels_file = 'processed_channels.txt'  # Файл для хранения обработанных каналов


def process_channels(message):
    with sq.connect("Chanelsyoutube_base.db") as con:
        cur = con.cursor()

        # Отримуємо дані користувача
        cur.execute("SELECT num_newchanel FROM users WHERE id = ?", (message.from_user.id,))
        user_data = cur.fetchone()
        if not user_data:
            bot.send_message(message.chat.id, "Виникла помилка. Будь ласка, спробуйте ще раз.")
            return

        num_newchanel = user_data[0]

        # Читаємо всі канали з файлу
        channels = get_all_channels()

        # Перевіряємо, чи є ще доступні канали
        if not channels:
            bot.send_message(message.chat.id, "На жаль, канали для обробки закінчилися. Спробуйте пізніше.")
            return

        # Отримуємо перший канал
        channel_line = channels[0]
        channel_parts = channel_line.split(',')
        if len(channel_parts) < 2:  # Перевірка формату
            bot.send_message(message.chat.id, "Сталася помилка з даними каналу. Зверніться до адміністратора.")
            return

        channel_id = channel_parts[0].strip()
        channel_name = channel_parts[1].strip()
        youtube_link = f'https://www.youtube.com/channel/{channel_id}'

        # Відправляємо канал користувачу
        bot.send_message(
            message.chat.id,
            f"Канал: {channel_name}\nПосилання: {youtube_link}"
        )
        # Відправляємо повідомлення з випадковим текстом
        bot.send_message(message.chat.id, get_random_channel_message(channel_name))

        # Видаляємо канал з основного файлу та додаємо в оброблені
        update_channel_files(channel_line)

        # Оновлюємо кількість виданих каналів користувачем у базі
        cur.execute("""
            UPDATE users
            SET num_newchanel = num_newchanel + 1
            WHERE id = ?
        """, (message.from_user.id,))
        con.commit()


# Функция для получения следующего канала из файла
def get_all_channels():
    try:
        with open(channels_file, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines() if line.strip()]  # Видаляємо порожні рядки
    except FileNotFoundError:
        print("Файл з каналами не знайдено.")
        return []
    except Exception as e:
        print(f"Помилка читання файлу: {e}")
        return []



# Функция для обновления файлов каналов
def update_channel_files(channel_line):
    global channels_file, processed_channels_file
    try:
        # Видаляємо рядок з основного файлу
        with open(channels_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        with open(channels_file, 'w', encoding='utf-8') as file:
            for line in lines:
                if line.strip() != channel_line.strip():
                    file.write(line)

        # Додаємо рядок до файлу оброблених каналів
        with open(processed_channels_file, 'a', encoding='utf-8') as processed_file:
            processed_file.write(channel_line + '\n')

    except Exception as e:
        print(f"Помилка оновлення файлів: {e}")


# Запуск бота
res = True
while res:
    try:
        bot.polling(skip_pending=True, none_stop=True)
        res = False
    except Exception as e:
        print(f'bot_stop: {e}', datetime.datetime.now())
        res = True

