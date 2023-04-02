import logging
import os
import time
import requests
import telegram
from dotenv import load_dotenv
import http

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
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Успешная отправке сообщения в Telegram')
    except Exception:
        logging.error('Ошибка отправки сообщения в Telegram')
        raise Exception


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
            logging.error(
                f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен.'
                f'Код ответа API: {response.status_code}'
            )
            raise Exception(f'Код ответа API: {response.status_code}')
        response = response.json()
    except requests.RequestException():
        raise Exception
    return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if "homeworks" in response:
        if type(response) is not dict:
            raise TypeError
        if type(response["homeworks"]) is not list:
            raise TypeError
    raise Exception('В response нет ключа homeworks '
                    'или ключа current_date')


def parse_status(homework):
    """Извлекает статус о конкретной домашней работе."""
    try:
        verdict = homework['status']
        homework_name = homework['homework_name'].replace(
            'username__', ''
        ).replace(
            '.zip', ''
        )
        return (
            f'Изменился статус проверки работы "{homework_name}". '
            f'{HOMEWORK_VERDICTS[verdict]}', verdict
        )
    except KeyError:
        logging.error("Неожиданный статус домашней работы, обнаруженный в ответе API")
        raise Exception
    except ValueError:
        logging.error("Неожиданный статус домашней работы, обнаруженный в ответе API")
        raise Exception


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
