import telebot
import math
import logging

from speechkit import speech_to_text, text_to_speech
from gpt import gpt, count_tokens
from config import TOKEN, MAX_TOKENS, MAX_AUDIO_BLOCKS, MAX_SYMBOLS, MAX_USERS, log_file
from db import select_all_users, add_new_user, get_tokens, update_tokens, update_stt_blocks, update_tts_symbols, create_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode="a"
)

create_database()
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    all_users = select_all_users()
    if not user_id in all_users:
        count = 0
        for i in all_users:
            count += 1
        if count > MAX_USERS:
            bot.send_message(message.from_user.id, "Извините, бот не доступен (превышено макс. кол.-во пользователей.")
            logging.info('Превышен лимит пользователей')
            return
        else:
            add_new_user(user_id)
            logging.info("Новый пользователь")
    bot.send_message(user_id, "Привет! Я могу сгенерировать пост для соцсетей по словестному описанию.\n"
                              "Отправь голосовое или текстовое сообщение с описанием поста\n"
                              "Можешь также воспользоваться доп. командами:\n"
                              "/stt - конвертирует речь в текст\n"
                              "/tts - конвертирует текст в речь")


@bot.message_handler(content_types=['text', 'voice', 'photo'])
def distributor(message: telebot.types.Message):
    user_id = message.from_user.id
    if message.content_type == 'voice':
        handle_voice(message)
    elif message.content_type == 'text':
        if message.text == '/stt':
            bot.send_message(user_id, 'Отправь аудио')
            bot.register_next_step_handler(message, stt)
        elif message.text == '/tts':
            bot.send_message(user_id, 'Введи текст, который надо озвучить')
            bot.register_next_step_handler(message, tts)
        elif message.text == '/debug':
            debug(message)
        else:
            handle_text(message)
    else:
        bot.send_message(user_id, 'Пожалуйста, отправьте текст или аудио')
        logging.error("Некорректный ввод")
        bot.register_next_step_handler(message, distributor)


def handle_voice(message: telebot.types.Message):
    user_id = message.from_user.id
    user_data = get_tokens(user_id)
    if user_data[0] > MAX_TOKENS or user_data[1] > MAX_AUDIO_BLOCKS or user_data[2] > MAX_SYMBOLS:
        bot.send_message(user_id, "К сожалению, у вас превышен лимит")
        logging.info("Превышен лимит")
        return
    stt_blocks = math.ceil(message.voice.duration/15)
    if stt_blocks > 2:
        bot.send_message(user_id, 'Аудио слишком длинное')
        return
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    status, text = speech_to_text(file)
    if not status:
        bot.send_message(user_id, text)
        logging.error(text)
        return
    tokens = count_tokens(text)
    if tokens > 50:
        bot.send_message(user_id, 'Сообщение слишком длинное')
        return
    status, answer = gpt(text)
    if not status:
        bot.send_message(user_id, "Извините, неполадки с gpt")
        logging.error(f'Ошибка с gpt - {answer}')
        return
    update_tokens(user_id, tokens)
    update_stt_blocks(user_id, stt_blocks)
    tts_symbols = len(answer)
    update_tts_symbols(user_id, tts_symbols)
    status, result = text_to_speech(answer)
    if not status:
        bot.send_message(user_id, result)
        logging.error(result)
        return
    bot.send_voice(user_id, result)


def handle_text(message: telebot.types.Message):
    user_id = message.from_user.id
    user_data = get_tokens(user_id)
    if user_data[0] > MAX_TOKENS:
        bot.send_message(user_id, "К сожалению, у вас превышен лимит токенов")
        logging.info("Превышен лимит токенов")
        return
    tokens = count_tokens(message.text)
    if tokens > 50:
        bot.send_message(user_id, 'Сообщение слишком длинное')
        return
    status, answer = gpt(message.text)
    if not status:
        bot.send_message(user_id, "Извините, неполадки с gpt")
        logging.error(f'Ошибка с gpt - {answer}')
        return
    update_tokens(user_id, tokens)
    bot.send_message(user_id, answer)


def tts(message: telebot.types.Message):
    user_id = message.from_user.id
    if message.content_type != 'text':
        bot.send_message(user_id, 'Пожалуйста, отправь текст')
        bot.register_next_step_handler(message, tts)
        logging.error("Некорректный ввод")
        return
    all_symbols = get_tokens(user_id)[2]
    if all_symbols >= MAX_SYMBOLS:
        bot.send_message(user_id, 'К сожалению, вы потратили все доступные символы')
        logging.info("Превышен лимит символов")
        return
    elif len(message.text) > 100:
        bot.send_message(user_id, 'Пожалуйста, отправьте менее длинное сообщение')
        bot.register_next_step_handler(message, tts)
        return
    status, result = text_to_speech(message.text)
    if not status:
        bot.send_message(user_id, result)
        logging.error(result)
        return
    update_tts_symbols(user_id, len(message.text))
    bot.send_voice(user_id, result)


def stt(message: telebot.types.Message):
    user_id = message.from_user.id
    if message.content_type != 'voice':
        bot.send_message(user_id, 'Пожалуйста, отправь аудио')
        logging.error("Некорректный ввод")
        bot.register_next_step_handler(message, stt)
        return
    audio_blocks = get_tokens(user_id)[1]
    if audio_blocks >= MAX_AUDIO_BLOCKS:
        bot.send_message(user_id, 'К сожалению, вы потратили все доступные блоки секунд')
        logging.info("Превышен лимит блоков секунд")
        return
    stt_blocks = math.ceil(message.voice.duration / 15)
    if stt_blocks > 2:
        bot.send_message(user_id, 'Аудио слишком длинное')
        return
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    status, result = speech_to_text(file)
    if not status:
        bot.send_message(user_id, result)
        logging.error(result)
        return
    update_stt_blocks(user_id, stt_blocks)
    bot.send_message(user_id, result)


def debug(message):
    try:
        with open("log_file.txt", "rb") as f:
            bot.send_document(message.chat.id, f)
        logging.info("Вызов режима отладки")
    except:
        bot.send_message(message.from_user.id, "Файл пуст")
        logging.error("этот файл был пуст")


bot.polling()
