import os
from telebot import *
from gigachat import GigaChat
import requests
import subprocess
import speech_recognition as sr
import datetime
import logging

from stt import audio_to_text
from config import token

bot = telebot.TeleBot(token)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s",
                    filename="logs.txt")


#старт
@bot.message_handler(commands=['start'])
def start(message):  
    keyboard = telebot.types.InlineKeyboardMarkup()
    button_start = telebot.types.InlineKeyboardButton(text='Приступим!', callback_data='get_started')
    button_help = telebot.types.InlineKeyboardButton(text='Я хочу узнать о тебе побольше.', callback_data='get_help')
    keyboard.add(button_start, button_help)
    bot.send_message(message.chat.id, "Привет!\nЯ бот, который поможет тебе улучшить свои кулинарные навыки!", reply_markup=keyboard) 

@bot.callback_query_handler(func=lambda call: call.data == 'get_help')
def help(call):
    message=call.message
    message_id = message.message_id
    chat_id = message.chat.id  
    keyboard = telebot.types.InlineKeyboardMarkup()
    button_get_started = telebot.types.InlineKeyboardButton(text='Приступим!', callback_data='get_started')
    keyboard.add(button_get_started)
    bot.edit_message_text(chat_id=chat_id,message_id=message_id, text="Я могу помочь тебе с рецептами, придумав их на основе твоих продуктов.\nЯ могу понимать тебя:\n   •текстом\n   •голосовым сообщением\n   •фото", 
                    reply_markup=keyboard)


#дебажим бота 
@bot.message_handler(commands=['debug'])
def send_logs(message):
    chat_id = message.chat.id
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_logs.log')
    if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        with open(log_path, 'rb') as log_file:
            bot.send_document(chat_id, log_file)
    else:
        bot.send_message(chat_id, 'Файл логов пуст')   


#указываем продукты текстом
@bot.callback_query_handler(func=lambda call: call.data == 'get_started')
def get_started(call):
    message = call.message
    global chat_id
    chat_id = message.chat.id  
    global message_id
    message_id = message.message_id
    button_text=telebot.types.InlineKeyboardButton(text='📰 текст', callback_data='text')
    button_audio=telebot.types.InlineKeyboardButton(text='🎤 аудио', callback_data='audio')
    button_photo=telebot.types.InlineKeyboardButton(text='📸 фото', callback_data='photo')
    keyboard1 = telebot.types.InlineKeyboardMarkup()
    keyboard1.add(button_text, button_audio, button_photo)
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, 
                         text='Для начала работы мне необходимо узнать из каких продуктов ты будешь готовить своё блюдо.\nПришли список продуктов текстом, голосовым сообщением или сфотографируй продукты на камеру.', reply_markup=keyboard1)

@bot.callback_query_handler(func=lambda call: call.data == 'text')
def text1(call):
    message=call.message
    bot.edit_message_text(chat_id=chat_id,message_id=message_id,
                        text='Напиши список продуктов, которые у тебя есть, а я попробую придумать для тебя рецепт .')
    bot.register_next_step_handler(message, text2)

@bot.message_handler(content_types=['message'])
def text2(message1):
    try:
        global keyboard_text
        keyboard_text = telebot.types.InlineKeyboardMarkup()
        button_other = telebot.types.InlineKeyboardButton(text='Придумай другое блюдо', callback_data='other')
        button_more = telebot.types.InlineKeyboardButton(text='Давай  больше рецептов!', callback_data='get_started')
        button_bye = telebot.types.InlineKeyboardButton(text='Я не хочу больше готовить. Пока!', callback_data='bye')
        keyboard_text.add(button_other, button_more, button_bye)
        with GigaChat(credentials='YTgzYThiZWYtMTU5Ny00ZmEyLWIzMTEtNGEwOTQ0MDc5MWYwOjA2MzlmY2QxLWMwNzQtNDkyNC1hNzg3LTI5MTFiMDYzNTczMQ==', verify_ssl_certs=False) as giga:
            response = giga.chat("Предложи рецепт блюда из продуктов: " + message1.text)
            bot.send_message(message1.chat.id,response.choices[0].message.content, reply_markup=keyboard_text)
    except TypeError:
        keyboard = telebot.types.InlineKeyboardMarkup()
        button_started = telebot.types.InlineKeyboardMarkup(text='Не хочу текстом.', callback_data = 'get_started')
        button_try = telebot.types.InlineKeyboardMarkup(text='Случайно перепутал :( . Давай заново.', callback_data = 'text')
        keyboard.add(button_started, button_try)
        bot.send_message(message1.from_user.id, "Я тебя не понимаю. Пришли мне текст.", reply_markup=keyboard)



# указываем продукты голосом
@bot.callback_query_handler(func=lambda call: call.data == 'audio')
def audio(call):
    message = call.message
    bot.edit_message_text(chat_id=chat_id, message_id=message_id,text='Пришли мне голосовое сообщение, в котором ты перечиляешь продукты, из которых  будешь готовить своё блюдо.')
    bot.register_next_step_handler(message, get_audio_messages)


@bot.message_handler(content_types=['voice'])
def get_audio_messages(message):
    try:
        print("Начинаем распознавание...")
        file_info = bot.get_file(message.voice.file_id)
        path = file_info.file_path
        fname = os.path.basename(path)
        
        # Получаем и сохраняем голосовое сообщение
        doc = requests.get(f'https://api.telegram.org/file/bot{token}/{file_info.file_path}')
        with open(fname + '.oga', 'wb') as f:
            f.write(doc.content)
        
        # Конвертируем .oga в .wav
        subprocess.run(['ffmpeg', '-i', fname + '.oga', fname + '.wav'])
        
        # Преобразуем аудио в текст
        global result
        result = audio_to_text(fname + '.wav')
        new_message = message
        new_message.text = result  
        text2(new_message)
  
    except sr.UnknownValueError:
        bot.send_message(message.from_user.id, "Не удалось распознать аудио.")
    except UnboundLocalError:
        keyboard = telebot.types.InlineKeyboardMarkup()
        button_started = telebot.types.InlineKeyboardMarkup(text='Не хочу голосовым сообщением.', callback_data = 'get_started')
        button_try = telebot.types.InlineKeyboardMarkup(text='Случайно перепутал :( . Давай заново.', callback_data = 'audio')
        keyboard.add(button_started, button_try)
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Пришли мне голосовое сообщение.", reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.from_user.id, "Произошла ошибка: " + str(e))
    

    finally:
        # Удаляем временные файлы
        if os.path.exists(fname + '.oga'):
            os.remove(fname + '.oga')
        if os.path.exists(fname + '.wav'):
            os.remove(fname + '.wav')



#указываем продукты фото
@bot.callback_query_handler(func=lambda call: call.data == 'photo')
def photo(call):
    message = call.message
    bot.edit_message_text(chat_id=chat_id, message_id=message_id,text='Пришли мне фото, на котором будут видны  продукты, из которых  будешь готовить своё блюдо.')
    bot.register_next_step_handler(message, get_photo_messages)

@bot.message_handler(content_types=['photo'])
def get_photo_messages(message):   
    fileID = message.photo[-1].file_id   
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Сохраняем загруженное изображение
    image_path = "image.jpg"
    with open(image_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # Используем GigaChat для распознавания ингредиентов на фото
    with GigaChat(credentials='YTgzYThiZWYtMTU5Ny00ZmEyLWIzMTEtNGEwOTQ0MDc5MWYwOjA2MzlmY2QxLWMwNzQtNDkyNC1hNzg3LTI5MTFiMDYzNTczMQ==', verify_ssl_certs=False) as giga:
        # Здесь предполагается, что GigaChat имеет метод для обработки изображений
        response = giga.chat("Предложи рецепт блюда из продуктов на фото.", image_path=image_path)
        bot.send_message(message.chat.id, response, reply_markup=keyboard_text)
    


#готовим другое блюдо
@bot.callback_query_handler(func=lambda call: call.data == 'other')
def other(call):
    message=call.message
    with GigaChat(credentials='YTgzYThiZWYtMTU5Ny00ZmEyLWIzMTEtNGEwOTQ0MDc5MWYwOjA2MzlmY2QxLWMwNzQtNDkyNC1hNzg3LTI5MTFiMDYzNTczMQ==', verify_ssl_certs=False) as giga:
        response = giga.chat("Предложи рецепт другого блюда из продуктов: " + message.text)
        bot.send_message(message.chat.id,response.choices[0].message.content, reply_markup=keyboard_text)


#прощаемся
@bot.callback_query_handler(func=lambda call: call.data == 'bye')
def bye(message):
    bot.send_message(message.from_user.id, "Пока! Если захотите приготовить что-то еще, обращайтесь. 😉")
    


# Запуск бота
bot.polling(none_stop=True, interval=0)
