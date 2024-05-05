import requests
import logging

from config import token, folder_id, log_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode="a"
)


def text_to_speech(text):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    data = {
        'text': text,  # текст, который нужно преобразовать в голосовое сообщение
        'lang': 'ru-RU',  # язык текста - русский
        'voice': 'madirus',  # голос Филиппа
        'speed': '1',
        'folderId': folder_id,
    }
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    response = requests.post(url=url, headers=headers, data=data)
    if response.status_code == 200:
        return True, response.content
    else:
        return False, "Ошибка с Speech Kit"


def speech_to_text(data):
    params = f'lang=ru-RU&folder_id={folder_id}'
    url = f'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.post(url=url, headers=headers, data=data)
    print(response.json())
    if response.status_code == 200:
        return  True, response.json()['result']
    else:
        return False, "Ошибка с Speech Kit"
