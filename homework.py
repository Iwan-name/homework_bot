import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import Updater

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    if PRACTICUM_TOKEN is None:
        # sys.exit('Практикум токен == None')
        raise 'Практикум токен == None'
    if TELEGRAM_TOKEN is None:
        sys.exit('Телеграмм токен == None')
    if TELEGRAM_CHAT_ID is None:
        sys.exit('Телеграм чат id == None')


def send_message(bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(timestamp):
    url = ENDPOINT
    headers = HEADERS
    payload = {'from_date': timestamp}
    homework_statuses = requests.get(url, headers=headers, params=payload)
    response = homework_statuses.json()
    return response


def check_response(response):
    if "homeworks" and "current_date" not in response:
        sys.exit('В response нет ключа homeworks или ключа current_date')


def parse_status(homework):
    verdict = homework['homeworks'][0]['status']
    homework_name = homework[
        'homeworks'
    ][0]['homework_name'].replace(
        'username__', ''
    ).replace(
        '.zip', ''
    )

    return f'Изменился статус проверки работы "{homework_name}". {verdict}', verdict


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    check_tokens()
    i = 0
    time.sleep(5)
    while i < 5:
        try:
            response = get_api_answer(0)
            check_response(response)
            message, verdict = parse_status(response)

            if verdict:
                verdict1 = verdict
                send_message(bot, message)
                i += 1

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
