"""
Модуль проверки статуса домашних заданий, находящихся на проверке.
Связывается с API сервиса, проверяет полученные данные. При наличии
обновленных статусов домашних заданий, отправляет сообщение о них в чат
Телеграм.
"""
import logging
import sys
import time
from http import HTTPStatus

import requests
import telegram

from exceptions import (TokenError, BotMalfunction, APIResponseError,
                        APIAccessError, DataError)
from settings import (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                      ENDPOINT, HEADERS, RETRY_TIME, HOMEWORK_STATUSES)

# Создание логера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s уровень %(levelname)s, функция %('
                              'funcName)s: %(message)s')
handler.setFormatter(formatter)


def send_message(bot, message: str) -> None:
    """Отправляет сообщение в чат."""
    try:
        if bot.send_message(TELEGRAM_CHAT_ID, message):
            logger.info('Сообщение в чат успешно отправлено.')
        else:
            logger.error(BotMalfunction.message)
    except BotMalfunction:
        logger.error(BotMalfunction.message)
    return None


def get_api_answer(timestamp: int) -> dict:
    """
    Делает запрос к эндпоинту API-сервиса.
    Возвращает полученные данные в виде словаря.
    """
    params: dict = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params,
                                timeout=10)

    except APIAccessError:
        logger.error(APIAccessError.message)
        raise APIAccessError(APIAccessError.message)

    if response.status_code != HTTPStatus.OK:
        logger.error(APIAccessError.message)
        raise APIAccessError(APIAccessError.message)

    if not response:
        logger.error(APIResponseError.message)
        raise APIResponseError(APIResponseError.message)

    try:
        response = response.json()
    except APIResponseError:
        logger.error(APIResponseError.message)
        raise APIResponseError(APIResponseError.message)

    response = dict(response)
    if not isinstance(response, dict):
        logger.error(APIResponseError.message)
        raise APIResponseError(APIResponseError.message)

    logger.info('Ответ от API получен. Словарь с данными передан '
                'дальше.')
    return response


def check_response(response: dict) -> list:
    """
    Проверяет словарь данных, полученный от API, на корректность.
    Возвращает список домашних работ.
    """
    if 'homeworks' not in response:
        logger.error(DataError.message)
        raise KeyError(DataError.message)

    hw_list = response.get('homeworks')

    if not isinstance(hw_list, list):
        logger.error(DataError.message)
        raise TypeError(DataError.message)

    logger.info('Словарь с данными проверен. Список домашних заданий '
                'передан дальше.')
    return hw_list


def parse_status(homework: dict) -> str:
    """
    Обрабатывает словарь с данными по домашнему заданию.
    Получает из словаря с данными статус задания и возвращает строку c
    названием задания и вердиктом, соответствующим статусу в словаре
    HOMEWORK_STATUSES.
    """
    if 'homework_name' not in homework or 'status' not in homework:
        logger.error(DataError.message)
        raise KeyError(DataError.message)

    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        logger.error(DataError.message)
        raise KeyError(DataError.message)

    verdict = HOMEWORK_STATUSES.get(homework_status)
    logger.info('Обновленный статус домашней работы получен. Вердикт '
                'передан дальше.')
    return (f'Изменился статус проверки работы "{homework_name}". '
            f'{verdict}')


def check_tokens() -> bool:
    """
    Проверяет доступность констант из settings.py.
    Возвращает булево значение.
    """
    if (not all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                 ENDPOINT, HEADERS,))
            or not isinstance(HOMEWORK_STATUSES, dict)
            or not all(key in HOMEWORK_STATUSES for key in (('approved',
                                                             'reviewing',
                                                             'rejected',))
                       )):
        return False
    logger.debug('Все токены и константы в порядке.')
    return True


def main():
    """
    Основная функция с главной логикой бота.
    Проверяет необходимые переменные, делает запрос к API, проверяет ответ и
    полученные данные; в случае наличия обновлений получает строку с
    вердиктом и отправляет ее в чат.
    """
    # бот Телеграм
    bot = telegram.Bot(TELEGRAM_TOKEN)

    # Проверка токенов и констант
    if not check_tokens():
        logger.critical(TokenError.message)
        send_message(bot, TokenError.message)
        raise TokenError

    # Метка времени для запроса к API
    timestamp = int(time.time()) - 86400
    # переменная для отслеживания повторяющихся ошибок
    error_message = ''

    while True:
        try:
            # Получение данных от API
            response = get_api_answer(timestamp)

            # Метка времени для последующих запросов
            timestamp = response.get('current_date') or timestamp

            # Выделение списка домашних заданий из полученных от API данных
            hw_list = check_response(response)

            # Проверка списка домашних заданий
            if hw_list:
                # Отправка обновленных статусов в чат
                for homework in hw_list:
                    verdict = parse_status(homework)
                    logger.info('Вердикт передан на отправку в чат.')
                    send_message(bot, verdict)
            else:
                logger.debug('Новых статусов домашних заданий нет.')

        except Exception as exception:
            # Проверка, было ли уже отправлено сообщение об этой ошибке
            if error_message != str(exception):
                send_message(bot, str(exception))
                error_message = str(exception)

        finally:
            time.sleep(RETRY_TIME or 600)


if __name__ == '__main__':
    main()
