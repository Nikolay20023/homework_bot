from http import HTTPStatus
import sys
import time
from dotenv import load_dotenv
import requests
import os
import telegram
import logging
import exception
import telegram.error

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
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.error('Ошибка в отправке сообщения.')
    except telegram.error.TelegramError as error:
        logging.error(f'Ошибка отправки сообщения telegram {error}')
        raise exception.TelegramError(
            f'Ошибка отправки сообщения telegram {error}'
        )
    else:
        logging.info('Удачная оправка сообщения.')


def get_api_answer(current_timestamp):
    """Запрашиваем ответ."""
    timestamp = current_timestamp or int(time.time())
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    try:
        logging.info(
            'Начинаем подключение к эндпоинту {url}, с параметрами'
            'headers = {headers}, params = {params}'
        )
        response = requests.get(**request_params)

        if response.status_code != HTTPStatus.OK:
            raise exception.TroubleResponse(
                'Ответ сервера не является успешным'
                f'requset params = {request_params};'
                f'Http_code = {response.status_code};'
                f'reason = {response.reason}; content = {response.text}'
            )

    except ConnectionError as error:
        logging.error('Сбои при запросе к эндпоинту.')
        raise exception.TroubleResponse(
            (
                'Во время подключения к {url} произошла ошибка'
                'непредвиденная ошибка: {error}'
                'headers = {headers}, params = {params}'
            ).format(
                error=error,
                **request_params
            )
        )

    response_json = response.json()
    return response_json


def check_response(response):
    """Делаем запросы."""
    logging.info('Начало проверки запроса')

    if type(response) != dict:
        logging.error('Неверный тип запроса')
        raise TypeError

    if not(('homeworks' in response) and ('current_date' in response)):
        raise KeyError(
            'В ответе API отсутсвуют необходимые ключи "homeworks" и/или'
            f'"Current_date", response = {response}'
        )
    if type(response['homeworks']) != list:
        error = 'Неверный тип возвращаемого результата'
        logging.error('Отсутвие ключей')
        raise TypeError(error)
    else:
        return response.get('homeworks')


def parse_status(homework):
    """ВЫборка по ключам."""
    logging.info('Старт работы функции "parse_status()".')
    if 'homework_name' not in homework:
        error = 'Отсутвует ключ "homework_name" в homework.'
        raise KeyError(error)

    elif 'status' not in homework:
        error = 'Отсутвует ключ "status" в homework.'
        raise exception.ApiKeyMissing(error)

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        error = 'Отсутвует homework_status в HOMEWORK_STATUSES.'
        raise exception.ApiKeyMissing(error)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """проверка переменных."""
    if not(PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        logging.critical('Отсутствие обязательных переменных.')
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not(check_tokens)():
        message = (
            'Отсутвуют обязательные переменные окружения: PRACTICUM_TOKEN,'
            'TELEGRAM_TOKEN, TELEGRAM_CHAD_ID,'
            'программа принудительно остановлена'
        )
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    current_report = {'name': '', 'output': ''}
    prev_report = current_report.copy()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date', current_timestamp)
            new_homework = check_response(response)

            if new_homework:
                current_report['name'] = new_homework[0]['homework_name']
                current_report['output'] = parse_status(new_homework[0])\

            else:
                current_report['output'] = (
                    f'За период от {current_timestamp} до настоящего момента'
                    'домашних работ нет.'
                )

            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy
            else:
                logging.debug('В ответе нет новых статусов')
            response_list = check_response(response)
            homework = response_list[0]
            send_message(bot, parse_status(homework))
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report['output'] = message
            logging.error(message, exc_info=True)
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
