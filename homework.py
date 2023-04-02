import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

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
    level='DEBUG',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='main.log',
    filemode='a',
    encoding='utf-8'
)


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    if PRACTICUM_TOKEN is None:
        logging.critical(
            'Отсутствует обязательная переменная '
            'окружения: PRACTICUM_TOKEN  Программа '
            'принудительно остановлена.'
        )
        raise Exception('Практикум токен == None')
    if TELEGRAM_TOKEN is None:
        logging.critical(
            'Отсутствует обязательная переменная '
            'окружения: TELEGRAM_TOKEN Программа '
            'принудительно остановлена.'
        )
        raise Exception('Телеграмм токен == None')
    if TELEGRAM_CHAT_ID is None:
        logging.critical(
            'Отсутствует обязательная переменная '
            'окружения: TELEGRAM_CHAT_ID Программа '
            'принудительно остановлена.'
        )
        raise Exception('Телеграм чат id == None')


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )


def get_api_answer(timestamp):
    """
    Функция делает запрос к эндпоинту API, проверяет статус ответа
    и возвращает response.
    """
    url = ENDPOINT
    headers = HEADERS
    payload = {'from_date': timestamp}
    homework_statuses = requests.get(
        url,
        headers=headers,
        params=payload
    )
    if homework_statuses.status_code == 200:
        response = homework_statuses.json()
        return response
    else:
        logging.error(
            f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {homework_statuses.status_code}'
        )


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if "homeworks" and "current_date" not in response:
        raise Exception('В response нет ключа homeworks '
                        'или ключа current_date')


def parse_status(homework):
    """
    Извлекает из информации о конкретной
    домашней работе статус этой работы.
    """
    verdict = homework['homeworks'][0]['status']
    if verdict in HOMEWORK_VERDICTS:
        homework_name = homework[
            'homeworks'
        ][0]['homework_name'].replace(
            'username__', ''
        ).replace(
            '.zip', ''
        )

        return (
            f'Изменился статус проверки работы "{homework_name}". '
            f'{HOMEWORK_VERDICTS[verdict]}', verdict
        )
    else:
        logging.error('Неожиданный статус домашней работы, '
                      'обнаруженный в ответе API')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    answer = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            message, verdict = parse_status(response)

            if verdict != answer:
                answer = verdict
                send_message(bot, message)
                logging.debug(
                    f'Сообщение с {message} отправлено в Telegram'
                )
                time.sleep(RETRY_PERIOD)
            else:
                logging.debug('Отсутствие в ответе новых статусов')
                time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)
            break


if __name__ == '__main__':
    main()
