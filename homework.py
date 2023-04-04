import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
import http

from exceptions import EnvironmentVariablesException

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

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='w',

)

logger = logging.getLogger(__name__)
handler = RotatingFileHandler(
    'main.log',
    maxBytes=50000000,
    backupCount=5,
    encoding='utf-8'
)
logger.addHandler(handler)


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
              'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
              'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
              }
    for key, value in tokens.items():
        if value is None:
            logger.critical(
                'Отсутствует обязательная переменная '
                f'окружения: {key}.Программа '
                'принудительно остановлена.'
            )
            raise EnvironmentVariablesException(f'{key}')


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.debug('Успешная отправке сообщения в Telegram')
    except Exception:
        logger.error('Ошибка отправки сообщения в Telegram')
        raise Exception('Ошибка отправки сообщения в Telegram')


def get_api_answer(timestamp):
    """
    Функция делает запрос к эндпоинту API и роверяет статус ответа.
    Возвращает response.
    """
    try:
        payload = {'from_date': timestamp}
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
        if response.status_code != http.HTTPStatus.OK:
            logger.error(
                f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен.'
                f'Код ответа API: {response.status_code}'
            )
            raise Exception(f'Код ответа API: {response.status_code}')
        response = response.json()
    except requests.RequestException():
        logger.error(
            'Проблема с соединением'
        )
    else:
        return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError
    if 'current_date' and 'homeworks' not in response:
        raise TypeError
    if not isinstance(response['homeworks'], list):
        raise TypeError


def parse_status(homework) -> str:
    """Извлекает статус о конкретной домашней работе."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе API домашки нет ключа homework_name')
    verdict = homework['status']
    if verdict not in HOMEWORK_VERDICTS:
        raise KeyError('API домашки возвращает недокументированный '
                       'статус домашней работы либо домашку без статуса.')
    homework_name = homework['homework_name'].replace(
        'username__', ''
    ).replace(
        '.zip', ''
    )
    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{HOMEWORK_VERDICTS[verdict]}'
    )


def main():
    """Основная логика работы бота."""
    if check_tokens():
        logger.critical('Ошибка при проверки '
                        'доступность переменных окружения')
        raise Exception('Ошибка при проверки '
                        'доступность переменных окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    answer = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response['homeworks']:
                verdict = response['homeworks'][0]['status']
                message = parse_status(response['homeworks'][0])
                if verdict != answer:
                    answer = verdict
                    send_message(bot, message)
                else:
                    logging.debug('Отсутствие в ответе новых статусов')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
