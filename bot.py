import os
import random
import time
import json
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton
) 

# Загрузка токена из .env файла
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Проверка токена
if not TOKEN:
    print("ОШИБКА: Токен бота не найден в переменных окружения!")
    print("Пожалуйста, создайте файл .env в корневой директории проекта")
    print("и добавьте в него строку: TELEGRAM_BOT_TOKEN=ваш_токен_бота")
    exit(1)

# Проверка формата токена
if not TOKEN or ':' not in TOKEN or len(TOKEN.split(':')) != 2:
    print("ОШИБКА: Неверный формат токена бота!")
    print("Токен должен быть в формате: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
    print(f"Текущий токен: {TOKEN[:10]}... (скрыт для безопасности)")
    exit(1)

print(f"Токен загружен: {TOKEN[:10]}... (скрыт для безопасности)")

bot = TeleBot(TOKEN)

# URL вашего веб-приложения
WEBAPP_URL = "https://piskapiska99.github.io/telegram-casino/"
CASES_WEBAPP_URL = "https://piskapiska99.github.io/telegram-casino/cases.html"

# Символы для слот-машины
SYMBOLS = ['💎', '💰', '⛏️']

# Множители выигрыша
MULTIPLIERS = {
    '💎💎💎': 5,    # Три алмаза
    '💰💰💰': 3,    # Три мешка с деньгами
    '⛏️⛏️⛏️': 2,    # Три кирки
    '💎💎': 2,      # Два алмаза
    '💰💰': 1.5,    # Два мешка с деньгами
    '⛏️⛏️': 1.2,    # Две кирки
}

# Путь к файлу с данными пользователей
USERS_DATA_FILE = 'users_data.json'

# База данных пользователей (в памяти)
users = {}

def load_users_data():
    """Загружает данные пользователей из файла"""
    global users
    try:
        if os.path.exists(USERS_DATA_FILE):
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
                # Конвертируем ключи из строк обратно в числа
                users = {int(k): v for k, v in users.items()}
    except Exception as e:
        print(f"Ошибка при загрузке данных пользователей: {e}")
        users = {}

def save_users_data():
    """Сохраняет данные пользователей в файл"""
    try:
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователей: {e}")

def get_user_balance(user_id):
    """Получение баланса пользователя"""
    if user_id not in users:
        users[user_id] = {'balance': 10000, 'inventory': []}
        save_users_data()
    return users[user_id]['balance']

def update_user_balance(user_id, amount):
    """Обновление баланса пользователя"""
    if user_id not in users:
        users[user_id] = {'balance': amount, 'inventory': []}
    else:
        users[user_id]['balance'] = amount
    save_users_data()

def calculate_win(symbols):
    # Преобразуем список символов в строку для проверки
    symbols_str = ''.join(symbols)
    
    # Проверяем комбинации из трёх символов
    if symbols_str in MULTIPLIERS:
        return MULTIPLIERS[symbols_str]
    
    # Проверяем комбинации из двух символов
    for i in range(len(SYMBOLS)):
        symbol = SYMBOLS[i]
        if symbols.count(symbol) >= 2:
            two_symbols = symbol * 2
            if two_symbols in MULTIPLIERS:
                return MULTIPLIERS[two_symbols]
    
    return 0

def get_main_keyboard():
    """Создает основную клавиатуру с кнопками для открытия веб-приложений"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = WebAppInfo(url=WEBAPP_URL)
    cases_web_app = WebAppInfo(url=CASES_WEBAPP_URL)
    keyboard.add(KeyboardButton(text="🎰 Открыть казино", web_app=web_app))
    keyboard.add(KeyboardButton(text="📦 Открыть кейсы", web_app=cases_web_app))
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cases_button = types.KeyboardButton(
        text="🎲 Открыть кейсы",
        web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/cases.html")
    )
    upgrade_button = types.KeyboardButton(
        text="⬆️ Апгрейд",
        web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/upgrade.html")
    )
    markup.add(cases_button, upgrade_button)
    
    bot.reply_to(
        message,
        "👋 Привет! Выбери действие:",
        reply_markup=markup
    )

@bot.message_handler(commands=['reset_balance'])
def reset_balance(message):
    # Проверяем, является ли пользователь администратором
    # Замените ADMIN_ID на ваш ID в Telegram
    ADMIN_ID = 123456789  # Замените на ваш ID
    
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
        return
    
    # Сбрасываем баланс всех пользователей на 10000 монет
    for user_id in users:
        users[user_id]['balance'] = 10000
    save_users_data()
    bot.reply_to(message, "Баланс всех пользователей сброшен на 10000 монет.")

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        user_id = message.from_user.id
        
        if data.get('action') == 'get_data' or data.get('action') == 'get_balance':
            # Отправляем текущий баланс пользователя
            balance = get_user_balance(user_id)
            response_data = {
                'balance': balance,
                'inventory': users.get(user_id, {}).get('inventory', [])
            }
            # Отправляем данные в формате строки JSON
            bot.send_message(user_id, f"web_app_data:{json.dumps(response_data)}")
            return

        if data.get('action') == 'update_data':
            # Обновляем баланс и инвентарь пользователя
            update_user_balance(user_id, data['balance'])
            if 'inventory' in data:
                if user_id not in users:
                    users[user_id] = {'balance': data['balance'], 'inventory': []}
                users[user_id]['inventory'] = data['inventory']
            save_users_data()
            
            # Отправляем подтверждение с обновленным балансом
            response_data = {
                'balance': get_user_balance(user_id),
                'inventory': users.get(user_id, {}).get('inventory', [])
            }
            bot.send_message(user_id, f"web_app_data:{json.dumps(response_data)}")
            
            # Отправляем сообщение о результате
            if 'won_item' in data:
                bot.reply_to(message, f"Вы получили: {data['won_item']['name']}")
            elif 'item_sold' in data:
                bot.reply_to(message, f"Вы продали {data['item_sold']['name']} за {data['item_sold']['value']} монет")
            return

        if data.get('action') == 'update_balance':
            # Обновляем только баланс
            update_user_balance(user_id, data['balance'])
            
            # Отправляем обновленный баланс
            response_data = {
                'balance': get_user_balance(user_id)
            }
            bot.send_message(user_id, f"web_app_data:{json.dumps(response_data)}")
            
            # Отправляем сообщение о результате
            if data.get('credit_taken'):
                bot.reply_to(message, "Вы взяли кредит в 1000 монет")
            elif 'win_amount' in data:
                if data['win_amount'] > 0:
                    bot.reply_to(message, f"Выигрыш: {data['win_amount']} монет (x{data['multiplier']})")
                else:
                    bot.reply_to(message, "Нет выигрышной комбинации")
            return

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler()
def handle_message(message):
    if message.text.lower() == "алина":
        bot.reply_to(message, "алик")
        return
    elif message.text.lower() == "олег":
        bot.reply_to(message, "король школы 46")
        return

@bot.message_handler(commands=['upgrade'])
def upgrade_command(message):
    user_id = str(message.from_user.id)
    inventory = db.get_inventory(user_id)
    balance = db.get_user(user_id)['balance']
    
    markup = types.InlineKeyboardMarkup()
    upgrade_button = types.InlineKeyboardButton(
        text="🔄 Открыть страницу апгрейда",
        web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/upgrade.html")
    )
    markup.add(upgrade_button)
    
    bot.reply_to(
        message,
        "🔄 Нажмите кнопку ниже, чтобы открыть страницу апгрейда предметов:",
        reply_markup=markup
    )

# Загружаем данные пользователей при старте бота
load_users_data()

# Запускаем бота
if __name__ == '__main__':
    print("Бот запущен...")
    try:
        # Проверяем подключение к API Telegram
        print("Проверка подключения к API Telegram...")
        bot_info = bot.get_me()
        print(f"Бот успешно подключен: @{bot_info.username}")
        print(f"Имя бота: {bot_info.first_name}")
        
        # Запускаем бота
        print("Запуск бота в режиме long polling...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        print("Проверьте правильность токена бота в файле .env")
        print("Токен должен быть в формате: TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
        print("\nУбедитесь, что:")
        print("1. Вы создали бота через @BotFather в Telegram")
        print("2. Вы скопировали правильный токен в файл .env")
        print("3. Токен не содержит лишних пробелов или символов")
        print("4. У вас есть доступ к интернету")
