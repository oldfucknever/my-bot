import telebot
from telebot import types
import threading
import time

API_TOKEN = '8939233058:AAHyx3fQ3BRo96FtF8eTaPNd5DI6RkCAwz4'
ADMIN_CHAT_ID = 2821082503  # Ваш ID для админ-чата
TOPIC_ID = 10171           # ID темы в чате

bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения очереди публикаций (сообщение_id: (данные_сообщения, чат_id, медиа_ид))
queue_messages = {}

@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle_opinion(message):
    user = message.from_user
    username = user.username if user.username else user.first_name
    
    # Формируем текст по вашему шаблону
    caption = f"— автор мнения: {username}\n\n"
    
    if message.content_type == 'text':
        caption += message.text
    elif message.caption:
        caption += message.caption
        
    caption += f"\n\nбот для мнений @{bot.get_me().username}"
    
    # Создаем клавиатуру с кнопками
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Принять сейчас", callback_data=f"approve_now_{message.message_id}"))
    markup.add(types.InlineKeyboardButton("Принять в очередь", callback_data=f"approve_queue_{message.message_id}"))
    markup.add(types.InlineKeyboardButton("Отклонить", callback_data=f"decline_{message.message_id}"))
    markup.add(types.InlineKeyboardButton("Заблокировать", callback_data=f"block_{message.from_user.id}"))

    # Отправляем сообщение в админ-чат/тему для модерации
    if message.content_type == 'photo':
        sent_message = bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, message_thread_id=TOPIC_ID)
    elif message.content_type == 'video':
        sent_message = bot.send_video(ADMIN_CHAT_ID, message.video.file_id, caption=caption, reply_markup=markup, message_thread_id=TOPIC_ID)
    else:
        sent_message = bot.send_message(ADMIN_CHAT_ID, caption, reply_markup=markup, message_thread_id=TOPIC_ID)

    # Сохраняем данные для возможной отложенной отправки
    queue_messages[message.message_id] = (message, sent_message.chat.id, message.content_type)

def publish_delayed(message_id):
    time.sleep(1200) # Задержка 20 минут (1200 секунд)
    if message_id in queue_messages:
        msg, chat_id, c_type = queue_messages.pop(message_id)
        # Здесь должна быть отправка в канал "арена"
        # Для примера отправляем обратно в чат с подтверждением
        bot.send_message(ADMIN_CHAT_ID, "Мнение опубликовано из очереди!", message_thread_id=TOPIC_ID)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, target_id = call.data.rsplit('_', 1)
    
    if 'approve_now' in action:
        # Логика публикации на арену сейчас
        bot.send_message(ADMIN_CHAT_ID, "Мнение опубликовано на арене!", message_thread_id=TOPIC_ID)
    elif 'approve_queue' in action:
        bot.send_message(ADMIN_CHAT_ID, "Мнение поставлено в очередь на 20 минут.", message_thread_id=TOPIC_ID)
        threading.Thread(target=publish_delayed, args=(int(target_id),)).start()
    elif 'decline' in action:
        bot.send_message(ADMIN_CHAT_ID, "Мнение отклонено модератором.", message_thread_id=TOPIC_ID)
    elif 'block' in action:
        bot.send_message(ADMIN_CHAT_ID, f"Пользователь с ID {target_id} заблокирован.", message_thread_id=TOPIC_ID)
        
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

bot.infinity_polling()
