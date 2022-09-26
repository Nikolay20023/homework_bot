from http import HTTPStatus
from logging.handlers import RotatingFileHandler
import time
from dotenv import load_dotenv
import requests
import os
import telegram
import logging
import exception

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename="main.log",
    filemode='w',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('work_log.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляем сообщения."""
    if bot.send_message(TELEGRAM_CHAT_ID, message):
        logger.error('Ошибка в отправке сообщения.')
    else:
        logger.info('Удачная оправка сообщения.')


def get_api_answer(current_timestamp):
    """Запрашиваем ответ."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if response.status_code != HTTPStatus.OK:
        error = 'status code вернул не 200'
        logger.error('Сбои при запросе к эндпоинту.')
        raise exception.TroubleResponse(error)

    response_json = response.json()
    return response_json


def check_response(response):
    """Делаем запросы."""
    if type(response) == str:
        error = 'Неверный тип возвращаемого результата'
        logger.error('Отсутвие ключей')
        raise TypeError(error)

    elif type(response['homeworks']) != list:
        error = 'Неверный тип возвращаемого результата'
        logger.error('Отсутвие ключей')
        raise TypeError(error)
    else:
        return response.get('homeworks')


def parse_status(homework):
    """ВЫборка по ключам."""
    logger.info('Старт работы функции "parse_status()".')
    if 'homework_name' not in homework:
        error = 'Отсутвует ключ "homework_name" в homework.'
        raise KeyError(error)

    elif 'status' not in homework:
        error = 'Отсутвует ключ "status" в homework.'
        raise exception.ApiKeyMissing(error)

    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """проверка переменных."""
    if not(PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        logger.critical('Отсутствие обязательных переменных.')
        return False
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 2710838
    if not(check_tokens)():
        raise exception.TroubleCheckToken
    while True:
        try:
            check_tokens()
            response = get_api_answer(current_timestamp)
            response_list = check_response(response)
            homework = response_list[0]
            send_message(bot, parse_status(homework))
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
