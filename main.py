import telebot
import sqlite3
from telebot import types
from datetime import datetime

API_TOKEN = "6704770874:AAERxHDHgimckXcfUfMOZcCSvlI_c5p2JVQ"
bot = telebot.TeleBot(API_TOKEN)

# Initialize the database connection
conn = sqlite3.connect('user_feedback.db', check_same_thread=False)
cursor = conn.cursor()

# Create User table
cursor.execute('''
CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER UNIQUE,
    first_name TEXT,
    last_name TEXT,
    birthdate TEXT,
    gender TEXT
)
''')

# Create Feedback table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    source TEXT,
    store TEXT,
    rating INTEGER,
    dislike TEXT,
    like TEXT,
    extra_comment TEXT,
    story TEXT,
    other_product TEXT,
    recommendation INTEGER,
    heard TEXT,
    timestamp TEXT,
    FOREIGN KEY(user_id) REFERENCES User(id)
)
''')

conn.commit()

user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_shop = types.InlineKeyboardButton("Shop", callback_data="start_shop")
    btn_brend = types.InlineKeyboardButton("Brend", callback_data="start_brend")
    markup.add(btn_shop, btn_brend)
    bot.send_message(chat_id, "Welcome! Please choose an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "start_shop")
def callback_shop(call):
    start_shop(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "start_brend")
def callback_brend(call):
    start_brend(call.message)

# Handlers for the bot commands
@bot.message_handler(commands=['shop'])
def start_shop(message):
    chat_id = message.chat.id
    if not is_user_register(chat_id):
       user_data[chat_id] = {'source': 'shop'}
       msg = bot.send_message(chat_id, "Вітаю! Будь ласка, введіть ваше ім'я:")
       bot.register_next_step_handler(msg, ask_last_name)
    else:
        bot.send_message(chat_id,"Ви вже зареєстровані!")

@bot.message_handler(commands=['brend'])
def start_brend(message):
    chat_id = message.chat.id
    if not is_user_register(chat_id):
       user_data[chat_id] = {'source': 'brend'}
       msg = bot.send_message(chat_id, "Вітаю! Будь ласка, введіть ваше ім'я:")
       bot.register_next_step_handler(msg, ask_last_name)
    else:
        bot.send_message(chat_id,"Ви вже зареєстровані!")

def is_user_register(chat_id):
    cursor.execute(
        '''
        SELECT id FROM User WHERE chat_id = ?
        ''', (chat_id,)
    )
    row = cursor.fetchone()
    return row is not None

#добавив валідацію на імʼя
def ask_last_name(message):
    chat_id = message.chat.id
    first_name=message.text
    if not first_name.isalpha():
        msg = bot.send_message(chat_id, "Будь ласка, введіть дійсне ім'я(лише літери)")
        bot.register_next_step_handler(msg, ask_last_name)
        return
    user_data[chat_id]['first_name'] = message.text
    msg = bot.send_message(chat_id, "Введіть ваше прізвище:")
    bot.register_next_step_handler(msg, ask_birthdate)

#добавив валідацію на прізвище
def ask_birthdate(message):
    chat_id = message.chat.id
    last_name = message.text
    if not last_name.isalpha():
        msg = bot.send_message(chat_id, "Будь ласка, введіть дійсне прізвище(лише літери):")
        bot.register_next_step_handler(msg, ask_birthdate)
        return
    user_data[chat_id]['last_name'] = message.text
    msg = bot.send_message(chat_id, "Введіть вашу дату народження (у форматі РРРР-ММ-ДД):")
    bot.register_next_step_handler(msg, ask_gender)

#добавив валідацію на рік народження
def validate_birthdate(message):
    chat_id = message.chat.id
    birthdate = message.text
    try:
        datetime.strptime(birthdate,'%Y-%m-%d')
    except ValueError:
        msg = bot.send_message(chat_id, "Будь ласка, введіть дійсну дату народження у форматі РРРР-ММ-ДД:")
        bot.register_next_step_handler(msg,validate_birthdate)
        return
    user_data[chat_id]['birthdate'] = birthdate
    ask_gender(message)

def ask_gender(message):
    chat_id = message.chat.id
    user_data[chat_id]['birthdate'] = message.text

    # Create buttons for gender selection
    markup = types.InlineKeyboardMarkup(row_width=2)
    male_btn = types.InlineKeyboardButton("Чоловіча", callback_data="gender_male")
    female_btn = types.InlineKeyboardButton("Жіноча", callback_data="gender_female")
    markup.add(male_btn, female_btn)

    bot.send_message(chat_id, "Оберіть вашу стать:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def handle_gender(call):
    chat_id = call.message.chat.id
    gender = call.data.split('_')[1]
    user_data[chat_id]['gender'] = gender

    save_user_data(chat_id)

    source = user_data[chat_id].get('source')
    if (source == 'shop'):
        ask_store(chat_id)
    elif (source == 'brend'):
        ask_brand_rating(chat_id)

def ask_store(chat_id):
    # Create buttons for store selection
    markup = types.InlineKeyboardMarkup(row_width=2)
    stores = ["Магазин 1", "Магазин 2", "Магазин 3", "Магазин 4", "Магазин 5", "Магазин 6"]
    buttons = [types.InlineKeyboardButton(store, callback_data=f'store_{store}') for store in stores]
    markup.add(*buttons)

    bot.send_message(chat_id, "В якому магазині був куплений товар?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('store_'))
def store_response(call):
    chat_id = call.message.chat.id
    store = call.data.split('_')[1]
    user_data[chat_id]['store'] = store

    # Create buttons for rating
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 11):
        markup.add(types.InlineKeyboardButton(str(i), callback_data=f'rating_{i}'))

    bot.send_message(chat_id, "Оцініть магазин від 1 до 10:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('rating_'))
def rating_response(call):
    chat_id = call.message.chat.id
    rating = int(call.data.split('_')[1])
    user_data[chat_id]['rating'] = rating
    if rating <= 6:
        ask_what_disliked(chat_id)
    elif rating == 7 or rating == 8:
        ask_what_improve(chat_id)
    elif rating >= 9:
        ask_what_liked(chat_id)

def ask_brand_rating(chat_id):
    # Create buttons for brand rating
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 11):
        markup.add(types.InlineKeyboardButton(str(i), callback_data=f'brand_rating_{i}'))

    bot.send_message(chat_id, "Оцініть бренд від 1 до 10:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('brand_rating_'))
def brand_rating_response(call):
    chat_id = call.message.chat.id
    rating = int(call.data.split('_')[2])
    user_data[chat_id]['rating'] = rating
    if rating <= 6:
        ask_what_disliked_brand(chat_id)
    else:
        msg = bot.send_message(chat_id, "Маєш ще що розповісти?")
        bot.register_next_step_handler(msg, ask_vitaminbomb_story)

def ask_what_disliked(chat_id):
    # Create buttons for "What did you dislike?"
    markup = types.InlineKeyboardMarkup(row_width=2)
    dislikes = ["Сервіс", "Швидкість обслуговування", "Асортимент", "Інше"]
    buttons = [types.InlineKeyboardButton(dislike, callback_data=f'dislike_{dislike}') for dislike in dislikes]
    markup.add(*buttons)
    bot.send_message(chat_id, "Що вам не сподобалось?", reply_markup=markup)

def ask_what_improve(chat_id):
    # Create buttons for "What can we improve?"
    markup = types.InlineKeyboardMarkup(row_width=2)
    improvements = ["Сервіс", "Швидкість обслуговування", "Асортимент", "Інше"]
    buttons = [types.InlineKeyboardButton(improvement, callback_data=f'improve_{improvement}') for improvement in improvements]
    markup.add(*buttons)
    bot.send_message(chat_id, "Що б ми могли покращити?", reply_markup=markup)

def ask_what_liked(chat_id):
    # Create buttons for "What did you like?"
    markup = types.InlineKeyboardMarkup(row_width=2)
    likes = ["Сервіс", "Швидкість обслуговування", "Асортимент", "Інше"]
    buttons = [types.InlineKeyboardButton(like, callback_data=f'like_{like}') for like in likes]
    markup.add(*buttons)
    bot.send_message(chat_id, "Що вам сподобалось?", reply_markup=markup)

def ask_what_disliked_brand(chat_id):
    # Create buttons for "What did you dislike about the brand?"
    markup = types.InlineKeyboardMarkup(row_width=2)
    dislikes = ["Ціна", "Недостатньо насичення в смаку", "Не знайшов підходящий смак", "Запах", "Проблеми з девайсом", "Інше"]
    buttons = [types.InlineKeyboardButton(dislike, callback_data=f'dislike_{dislike}') for dislike in dislikes]
    markup.add(*buttons)
    bot.send_message(chat_id, "Що вам не сподобалось в бренді?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dislike_'))
def dislike_response(call):
    chat_id = call.message.chat.id
    dislike = call.data.split('_')[1]
    user_data[chat_id]['dislike'] = dislike
    msg = bot.send_message(chat_id, "Маєш ще що розповісти?")
    bot.register_next_step_handler(msg, ask_vitaminbomb_story)

@bot.callback_query_handler(func=lambda call: call.data.startswith('like_'))
def like_response(call):
    chat_id = call.message.chat.id
    like = call.data.split('_')[1]
    user_data[chat_id]['like'] = like
    msg = bot.send_message(chat_id, "Маєш ще що розповісти?")
    bot.register_next_step_handler(msg, ask_if_heard_about_program)

def ask_if_heard_about_program(message):
    chat_id = message.chat.id
    user_data[chat_id]['extra_comment'] = message.text

    # Create buttons for "Did you hear about the discount program?"
    markup = types.InlineKeyboardMarkup(row_width=2)
    heard_options = ["Так", "Ні"]
    buttons = [types.InlineKeyboardButton(option, callback_data=f'heard_{option}') for option in heard_options]
    markup.add(*buttons)

    bot.send_message(chat_id, "Чи розповіли тобі про програму знижок?", reply_markup=markup)

def ask_vitaminbomb_story(message):
    chat_id = message.chat.id
    user_data[chat_id]['extra_comment'] = message.text

    # Create buttons for "If you were to describe your Vitaminbomb story in one sentence, it would be:"
    markup = types.InlineKeyboardMarkup(row_width=2)
    story_options = [
        "Я використовую тільки Vitaminbomb",
        "Більше Vitaminbomb чи інші",
        "50.50",
        "Більше конкуретна",
        "Не використовую такі девайси"
    ]
    buttons = [types.InlineKeyboardButton(option, callback_data=f'story_{option}') for option in story_options]
    markup.add(*buttons)

    bot.send_message(chat_id, "Якщо попросимо описати твою Vitaminbomb-історію одним реченням, це буде:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('story_'))
def story_response(call):
    chat_id = call.message.chat.id
    story = call.data.split('_')[1]
    user_data[chat_id]['story'] = story

    if story == "Я використовую тільки Vitaminbomb":
        ask_recommendation(chat_id)
    else:
        ask_other_products(chat_id)

def ask_other_products(chat_id):
    # Create buttons for "What other products do you use?"
    markup = types.InlineKeyboardMarkup(row_width=2)
    products = [f"Засіб {i}" for i in range(1, 6)]
    buttons = [types.InlineKeyboardButton(product, callback_data=f'product_{product}') for product in products]
    markup.add(*buttons)

    bot.send_message(chat_id, "Які інші засоби ти використовуєш?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def product_response(call):
    chat_id = call.message.chat.id
    product = call.data.split('_')[1]
    user_data[chat_id]['other_product'] = product
    ask_recommendation(chat_id)

def ask_recommendation(chat_id):
    # Create buttons for "How likely are you to recommend our brand?"
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(0, 101, 25):
        markup.add(types.InlineKeyboardButton(str(i), callback_data=f'recommend_{i}'))

    bot.send_message(chat_id, "Наскільки ймовірно ти порекомендуєш наш бренд?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('recommend_'))
def recommend_response(call):
    chat_id = call.message.chat.id
    recommendation = int(call.data.split('_')[1])
    user_data[chat_id]['recommendation'] = recommendation
    save_feedback(chat_id)
    send_final_thanks(chat_id)

def save_user_data(chat_id):
    data = user_data[chat_id]

    cursor.execute('''
        INSERT OR IGNORE INTO User (
            chat_id, first_name, last_name, birthdate, gender
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        chat_id,
        data.get('first_name', ''),
        data.get('last_name', ''),
        data.get('birthdate', ''),
        data.get('gender', '')
    ))

    conn.commit()

def save_feedback(chat_id):
    data = user_data[chat_id]
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        SELECT id FROM User WHERE chat_id = ?
    ''', (chat_id,))
    user_id = cursor.fetchone()[0]

    cursor.execute('''
        INSERT INTO Feedback (
            user_id, source, store, rating, dislike, like, extra_comment, story, other_product, recommendation, heard, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        data.get('source', ''),
        data.get('store', ''),
        data.get('rating', ''),
        data.get('dislike', ''),
        data.get('like', ''),
        data.get('extra_comment', ''),
        data.get('story', ''),
        data.get('other_product', ''),
        data.get('recommendation', ''),
        data.get('heard', ''),
        timestamp
    ))

    conn.commit()

def send_final_thanks(chat_id):
    bot.send_message(chat_id, "Дякуємо за ваш відгук!")

# Start the bot
bot.polling(none_stop=True)
