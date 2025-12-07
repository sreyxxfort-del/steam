import telebot
from telebot import types
import random
import json
import os # Для проверки существования файла

# --- КОНФИГУРАЦИЯ ---
# !!! ОБЯЗАТЕЛЬНО ЗАМЕНИТЕ ЭТИ ЗНАЧЕНИЯ !!!
TOKEN = '8491715276:AAFj6vlpY_GtAFPnxLdT6vODwmBvSxrB2e8' 
ADMIN_ID = 7896097894  # !!! ЗАМЕНИТЕ НА ВАШ АЙДИ ТЕЛЕГРАМ !!!
DATA_FILE = 'accounts.json' # Имя файла для хранения данных
# ----------------------------------------
bot = telebot.TeleBot(TOKEN)

# --- БАЗА ДАННЫХ (инициализация, будет перезаписана при загрузке) ---
ACCOUNTS = {}
STEAM_KEYS = []
OPENED_FOLDERS = []

# --- ФУНКЦИИ УПРАВЛЕНИЯ JSON (ВОССТАНОВЛЕНЫ) ---

def load_data():
    """Загружает данные из JSON файла."""
    global ACCOUNTS, STEAM_KEYS, OPENED_FOLDERS
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ACCOUNTS = data.get('accounts', {})
                STEAM_KEYS = data.get('steam_keys', [])
                # Если opened_folders нет в файле, используем все ключи из ACCOUNTS по умолчанию
                OPENED_FOLDERS = data.get('opened_folders', list(ACCOUNTS.keys()))
        except json.JSONDecodeError:
            print("⚠️ Ошибка чтения JSON файла. Использую пустую базу.")
            ACCOUNTS = {}
            STEAM_KEYS = []
            OPENED_FOLDERS = []
    else:
        # Создаем пустую базу и сохраняем ее
        ACCOUNTS = {}
        STEAM_KEYS = []
        OPENED_FOLDERS = []
        save_data() 
    
    print("✅ Данные успешно загружены.")

def save_data():
    """Сохраняет текущие данные в JSON файл."""
    data = {
        'accounts': ACCOUNTS,
        'steam_keys': STEAM_KEYS,
        'opened_folders': OPENED_FOLDERS
    }
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            # indent=4 для красивого форматирования, ensure_ascii=False для кириллицы
            json.dump(data, f, indent=4, ensure_ascii=False)
        # print("✅ Данные успешно сохранены.") # Закомментировано, чтобы не спамить в консоль
    except Exception as e:
        print(f"❌ Ошибка при сохранении данных в JSON: {e}")


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def is_admin(message):
    """Проверка, является ли пользователь админом"""
    return message.from_user.id == ADMIN_ID

def get_random_account_response(call_id=None):
    """Выбирает случайный аккаунт и генерирует текст/кнопки."""
    all_accounts = [acc for key in ACCOUNTS for acc in ACCOUNTS[key]]
    
    if not all_accounts:
        if call_id:
            bot.answer_callback_query(call_id, text="В базе нет ни одного аккаунта!", show_alert=True)
        
        empty_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ назад", callback_data='menu_steam_game'))
        return "❌ В базе нет ни одного аккаунта!", empty_markup, None

    random_account = random.choice(all_accounts)
    status_text = "✅ Работает" if random_account['status'] == '1' else "❌ Не работает"
    
    response_text = (
        f"Вам нужен рандомный аккаунт? вот:\n\n"
        f"👤 **Login:** `{random_account['login']}` (нажмите, чтобы скопировать)\n"
        f"🔑 **Password:** `{random_account['password']}` (нажмите, чтобы скопировать)\n"
        f"📩 **Status:** {status_text}\n"
        f"📚 **Library:** {random_account['library']}\n\n"
        f"Напоминание: Аккаунты могут быть использованы одновременно, будьте терпеливы."
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🎲 Крутить (Другой аккаунт)", callback_data='reroll_random')) 
    markup.add(types.InlineKeyboardButton("⬅️ назад", callback_data='menu_steam_game'))

    return response_text, markup, random_account

# --- ФУНКЦИИ КЛАВИАТУР (без изменений) ---

def create_main_keyboard(is_user_admin):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    keyboard.add(types.KeyboardButton('🎮 Steam Game')) 
    
    keyboard.add(
        types.KeyboardButton('🔑 Steam Key'), 
        types.KeyboardButton('❓ Помощь'),
        types.KeyboardButton('🔄 Перезапустить бота')
    )
    
        
    return keyboard

def get_game_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for folder in OPENED_FOLDERS:
        markup.add(types.InlineKeyboardButton(folder, callback_data=f'game_folder_{folder}'))

    if ACCOUNTS: 
        markup.add(types.InlineKeyboardButton("🎲 Random Account", callback_data='game_random'))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад в Главное Меню", callback_data='menu_main'))
    return markup


# --- ОБРАБОТЧИК КОМАНД /start и /menu (без изменений) ---

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    user_name = message.from_user.first_name if message.from_user.first_name else "пользователь"
    admin_status = is_admin(message) 
    
    keyboard = create_main_keyboard(admin_status)
    
    welcome_text = f"Здравствуйте! **{user_name}** выберите пожалуйста кнопку!"
    if admin_status:
        welcome_text += "\n\n**[!] Вы Администратор.** Вам доступны дополнительные команды на клавиатуре."
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# --- ОБРАБОТЧИК КЛАВИАТУРНЫХ ТЕКСТОВ (без изменений) ---

@bot.message_handler(func=lambda message: message.text in ['🎮 Steam Game', '🔑 Steam Key', '❓ Помощь', '🔄 Перезапустить бота'])
def handle_menu_text_buttons(message):
    text = message.text
    chat_id = message.chat.id
    
    if text == '🎮 Steam Game':
        bot.send_message(
            chat_id, 
            "Вы выбрали steam игры, теперь выберите игру:", 
            reply_markup=get_game_menu() 
        )
        
    elif text == '🔑 Steam Key':
        keys_text = "Вы выбрали steam ключи, вот все рабочие ключи:\n\n" + "\n".join(
            [f"🔑 `{key}`" for key in STEAM_KEYS]
        ) if STEAM_KEYS else "❌ На данный момент рабочие ключи отсутствуют."
        
        bot.send_message(
            chat_id, 
            keys_text, 
            parse_mode='Markdown'
        )

    elif text == '❓ Помощь':
        help_text = (
            "Если у вас **не работает аккаунт** или возникли вопросы по его использованию, "
            "напишите: **@mentyly**\n\n"
            "⚠️ Что касается ключей, мы не можем гарантировать их работу после получения."
        )
        bot.send_message(
            chat_id, 
            help_text, 
            parse_mode='Markdown'
        )
        
    elif text == '🔄 Перезапустить бота':
        bot.send_message(
            chat_id, 
            "✅ Вы успешно **перезапустили бота!**",
            parse_mode='Markdown'
        )


# --- ОБРАБОТЧИК INLINE-КНОПОК (CALLBACKS) (без изменений) ---

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    data = call.data
    
    try:
        if data == 'menu_main':
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="Выберите, что вас интересует:",
                reply_markup=get_game_menu() 
            )
        
        elif data == 'menu_steam_game':
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="Вы выбрали steam игры, теперь выберите игру:",
                reply_markup=get_game_menu()
            )
            
        elif data.startswith('game_folder_'):
            folder_name = data.split('_')[2]
            accounts_list = ACCOUNTS.get(folder_name)
            
            if not accounts_list or folder_name not in OPENED_FOLDERS:
                bot.answer_callback_query(call.id, text=f"Ошибка: Папка {folder_name} закрыта или пуста.", show_alert=True)
                return

            account = random.choice(accounts_list)
            status_text = "✅ Работает" if account['status'] == '1' else "❌ Не работает"
            
            response_text = (
                f"О, Вам нужен аккаунт, где будет **{folder_name}**? вот:\n\n"
                f"👤 **Login:** `{account['login']}` (нажмите, чтобы скопировать)\n" 
                f"🔑 **Password:** `{account['password']}` (нажмите, чтобы скопировать)\n"
                f"📩 **Status:** {status_text}\n"
                f"📚 **Library:** {account['library']}\n\n"
                f"Напоминание: Аккаунты могут быть использованы одновременно, будьте терпеливы."
            )
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=response_text,
                reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ назад", callback_data='menu_steam_game')),
                parse_mode='Markdown'
            )
        
        elif data == 'game_random':
            response_text, markup, _ = get_random_account_response(call.id)
            
            if "❌ В базе нет" in response_text:
                return
                
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=response_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )

        elif data == 'reroll_random':
            bot.answer_callback_query(call.id, text="Крутим новый аккаунт... 🎲")
            response_text, markup, _ = get_random_account_response()
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=response_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, text="Произошла ошибка при обработке запроса.", show_alert=True)


# --- АДМИНСКИЕ КОМАНДЫ (С ВЫЗОВОМ save_data()) ---

# /folder [ИМЯ] [Логин] [Пароль] [1/2 Статус] [Библиотека]
@bot.message_handler(commands=['folder'], func=is_admin)
def add_account(message):
    try:
        args = message.text.split()
        if len(args) < 6:
            bot.reply_to(message, "Ошибка формата. Используйте: `/folder [ИМЯ] [Логин] [Пароль] [1/2 Статус] [Библиотека]`", parse_mode='Markdown')
            return

        folder_name = args[1]
        login = args[2]
        password = args[3]
        status = args[4]
        library = ' '.join(args[5:])

        # ПРОВЕРКА НА ДУБЛИКАТ
        for folder_name_check in ACCOUNTS:
            for existing_account in ACCOUNTS[folder_name_check]:
                if existing_account['login'] == login:
                    bot.reply_to(
                        message, 
                        f"❌ **Ошибка добавления!** Аккаунт с логином **{login}** уже существует в папке **{folder_name_check}**.", 
                        parse_mode='Markdown'
                    )
                    return 

        new_account = {'login': login, 'password': password, 'status': status, 'library': library}

        if folder_name not in ACCOUNTS:
            ACCOUNTS[folder_name] = []
            OPENED_FOLDERS.append(folder_name) 

        ACCOUNTS[folder_name].append(new_account)
        save_data() # <--- СОХРАНЕНИЕ
        bot.reply_to(message, f"✅ Аккаунт `{login}` успешно добавлен в папку **{folder_name}**.", parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка: {e}")

# /zakrit [названия кнопки]
@bot.message_handler(commands=['zakrit'], func=is_admin)
def close_folder(message):
    try:
        folder_name = message.text.split()[1]
        if folder_name in OPENED_FOLDERS:
            OPENED_FOLDERS.remove(folder_name)
            save_data() # <--- СОХРАНЕНИЕ
            bot.reply_to(message, f"✅ Кнопка **{folder_name}** успешно деактивирована!")
        else:
            bot.reply_to(message, f"⚠️ Кнопка **{folder_name}** уже была закрыта или не существует в открытых.")
    except Exception:
        bot.reply_to(message, "Ошибка формата. Используйте: `/zakrit [ИМЯ]`")

# /open [ названия кнопки]
@bot.message_handler(commands=['open'], func=is_admin)
def open_folder(message):
    try:
        folder_name = message.text.split()[1]
        if folder_name not in ACCOUNTS:
            bot.reply_to(message, f"⚠️ Папки **{folder_name}** не существует в базе.")
            return

        if folder_name not in OPENED_FOLDERS:
            OPENED_FOLDERS.append(folder_name)
            save_data() # <--- СОХРАНЕНИЕ
            bot.reply_to(message, f"✅ Кнопка **{folder_name}** успешно активирована!")
        else:
            bot.reply_to(message, f"⚠️ Кнопка **{folder_name}** уже была открыта.")
    except Exception:
        bot.reply_to(message, "Ошибка формата. Используйте: `/open [ИМЯ]`")

# /bib [логин] [текст_библиотеки]
@bot.message_handler(commands=['bib'], func=is_admin)
def update_library(message):
    try:
        args = message.text.split(' ', 2)
        if len(args) < 3:
            bot.reply_to(message, "Ошибка формата. Используйте: `/bib [Логин_Аккаунта] [Новая_Библиотека]`", parse_mode='Markdown')
            return

        target_login = args[1]
        new_library_text = args[2]
        
        found = False
        
        for folder_name in ACCOUNTS:
            for account in ACCOUNTS[folder_name]:
                if account['login'] == target_login:
                    account['library'] = new_library_text
                    found = True
                    break 
            if found:
                break 

        if found:
            save_data() # <--- СОХРАНЕНИЕ
            bot.reply_to(message, f"✅ Библиотека для аккаунта **{target_login}** успешно изменена на: `{new_library_text}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ Аккаунт с логином **{target_login}** не найден ни в одной папке.", parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка при обновлении библиотеки: {e}")
        
# /izmenit [Текущий_Логин] [Новый_Логин] [Новый_Пароль] [1/2 Статус]
@bot.message_handler(commands=['izmenit'], func=is_admin)
def edit_account(message):
    try:
        args = message.text.split()
        if len(args) != 5:
            bot.reply_to(
                message, 
                "❌ **Ошибка формата.** Используйте:\n`/izmenit [ТЕКУЩИЙ_ЛОГИН] [НОВЫЙ_ЛОГИН] [НОВЫЙ_ПАРОЛЬ] [1/2 СТАТУС]`", 
                parse_mode='Markdown'
            )
            return

        target_login = args[1]
        new_login = args[2]
        new_password = args[3]
        new_status = args[4]

        if new_status not in ['1', '2']:
            bot.reply_to(message, "❌ **Неверный статус.** Используйте только **1** (работает) или **2** (не работает).", parse_mode='Markdown')
            return

        found = False
        
        for folder_name in ACCOUNTS:
            for account in ACCOUNTS[folder_name]:
                if account['login'] == target_login:
                    account['login'] = new_login
                    account['password'] = new_password
                    account['status'] = new_status
                    found = True
                    break
            if found:
                break

        if found:
            save_data() # <--- СОХРАНЕНИЕ
            status_text = "✅ Работает" if new_status == '1' else "❌ Не работает"
            bot.reply_to(
                message, 
                f"✅ Аккаунт **{target_login}** успешно изменен.\n"
                f"Новый Логин: `{new_login}`\n"
                f"Новый Пароль: `{new_password}`\n"
                f"Новый Статус: {status_text}",
                parse_mode='Markdown'
            )
        else:
            bot.reply_to(message, f"❌ Аккаунт с логином **{target_login}** не найден.", parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка при изменении аккаунта: {e}")

# /delete [Логин_Аккаунта]
@bot.message_handler(commands=['delete'], func=is_admin)
def delete_account(message):
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Ошибка формата. Используйте: `/delete [Логин_Аккаунта]`", parse_mode='Markdown')
            return

        target_login = args[1]
        found = False
        
        for folder_name in list(ACCOUNTS.keys()): 
            initial_count = len(ACCOUNTS.get(folder_name, []))
            
            ACCOUNTS[folder_name] = [
                account for account in ACCOUNTS[folder_name] 
                if account['login'] != target_login
            ]
            
            final_count = len(ACCOUNTS.get(folder_name, []))
            
            if initial_count > final_count:
                found = True
                
            if not ACCOUNTS[folder_name] and folder_name in ACCOUNTS:
                 del ACCOUNTS[folder_name]
                 if folder_name in OPENED_FOLDERS:
                    OPENED_FOLDERS.remove(folder_name)
            
            if found:
                break 

        if found:
            save_data() # <--- СОХРАНЕНИЕ
            bot.reply_to(message, f"✅ Аккаунт **{target_login}** успешно удален из базы.", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ Аккаунт с логином **{target_login}** не найден в базе.", parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка при удалении аккаунта: {e}")

# /key [текст]
@bot.message_handler(commands=['key'], func=is_admin)
def add_key(message):
    try:
        key_text = message.text.split(' ', 1)[1].strip()
        if key_text not in STEAM_KEYS:
            STEAM_KEYS.append(key_text)
            save_data() # <--- СОХРАНЕНИЕ
            bot.reply_to(message, f"✅ Ключ `{key_text}` успешно добавлен.")
        else:
            bot.reply_to(message, f"⚠️ Ключ `{key_text}` уже существует.")
    except IndexError:
        bot.reply_to(message, "Ошибка формата. Используйте: `/key [КЛЮЧ]`")

# /deletekey [КЛЮЧ]
@bot.message_handler(commands=['deletekey'], func=is_admin)
def delete_key(message):
    try:
        key_text = message.text.split(' ', 1)[1].strip()
        if key_text in STEAM_KEYS:
            STEAM_KEYS.remove(key_text)
            save_data() # <--- СОХРАНЕНИЕ
            bot.reply_to(message, f"✅ Ключ `{key_text}` успешно удален.")
        else:
            bot.reply_to(message, f"⚠️ Ключ `{key_text}` не найден.")
    except IndexError:
        bot.reply_to(message, "Ошибка формата. Используйте: `/deletekey [КЛЮЧ]`")

# --- ЗАПУСК БОТА ---
if __name__ == '__main__':
    load_data() # <--- Загружаем данные при старте
    print("Бот запущен. Данные сохраняются в accounts.json.")
    bot.polling(none_stop=True)