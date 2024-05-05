import requests
import logging
from config import token, folder_id, SYSTEM_PROMPT, log_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode="a"
)

def gpt(task):
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "300"
        },
        "messages": [
            {
                "role": "system",
                "text": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "text": task
            }
        ]
    }

    try:
        response = requests.post(
            url='https://llm.api.cloud.yandex.net/foundationModels/v1/completion',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json=data
        )
        if response.status_code == 200:
            return True, response.json()["result"]["alternatives"][0]["message"]["text"]
        else:
            logging.error(f"Ошибка получения ответа от gpt: {response.status_code}")
            return False, response.status_code
    except:
        logging.error("Ошибка отправки запроса к gpt")


def count_tokens(message):
    print(message)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
       "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
       "maxTokens": "200",
       "messages": [{'role' : 'user', 'text' : message}]
    }
    count = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
            json=data,
            headers=headers
    )
    return len(count.json()["tokens"])


#print(count_tokens('Привет'))
