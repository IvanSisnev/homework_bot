"""
Модуль проверки статуса домашних заданий, находящихся на проверке.
Связывается с API сервиса, проверяет полученные данные. При наличии
обновленных статусов домашних заданий, отправляет сообщение о них в чат
Телеграм.
"""
import logging
import sys
import time

import requests
import telegram

from exceptions import *
from settings import *


# Создание логера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
handler = logging.FileHandler('log.txt', encoding=ENCODING)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s уровень %(levelname)s, функция %('
                              'funcName)s: %(message)s')
handler.setFormatter(formatter)


def send_message(bot, message: str) -> None:
    """
    Отправляет сообщение в чат.
    :param bot: экземпляр класса telegram.Bot
    :param message: текст сообщения
    """
    if bot.send_message(TELEGRAM_CHAT_ID, message):
        logger.info('Сообщение в чат успешно отправлено.')
    else:
        logger.error(BotMalfunction.message)
    return None

def get_api_answer(timestamp: int) -> dict:
    """
    Делает запрос к эндпоинту API-сервиса и возвращает полученные данные в
    виде словаря.
    :param timestamp: метка времени
    :return response: словарь данными
    """
    params: dict = {'from_date': timestamp}

    response = requests.get(ENDPOINT, headers=HEADERS, params=params,
                            timeout=10)

    if response.status_code != 200:
        logger.error(APIAccessError.message)
        raise APIAccessError

    response = dict(response.json())

    if not isinstance(response, dict):
        logger.error(APIResponseError.message)
        raise APIResponseError

    logger.info('Ответ от API получен. '
                'Словарь с данными передан дальше.')
    return response


def check_response(response: dict) -> list:
    """
    Проверяет данные, полученные от API, на корректность и возвращает список
    домашних работ.
    :param response: словарь с данными
    :return: hw_list: список домашних работ
    """
    if 'homeworks' not in response:
        logger.error(DataError.message)
        raise KeyError

    hw_list = response.get('homeworks')

    if not isinstance(hw_list, list):
        logger.error(DataError.message)
        raise TypeError

    logger.info('Словарь с данными проверен. Список домашних заданий '
                'передан дальше.')
    return hw_list


def parse_status(homework: dict) -> str:
    """
    Получает из словаря с данными домашнего задания его статус и возвращает
    строку c названием задания и вердиктом, соответствующим статусу в словаре
    HOMEWORK_STATUSES.
    :param homework: словарь с данными домашнего задания
    :return verdict: строка с вердиктом
    """
    if 'homework_name' not in homework or 'status' not in homework:
        logger.error(DataError.message)
        raise KeyError

    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        logger.error(DataError.message)
        raise KeyError

    verdict = HOMEWORK_STATUSES.get(homework_status)
    logger.info('Обновленный статус домашней работы получен. Вердикт '
                'передан дальше.')
    return (f'Изменился статус проверки работы "{homework_name}". '
            f'{verdict}')


def check_tokens() -> bool:
    """
    Проверяет доступность констант из settings.py.
    :return: bool
    """
    if not all(
            (
                    PRACTICUM_TOKEN,
                    TELEGRAM_TOKEN,
                    TELEGRAM_CHAT_ID,
                    ENDPOINT,
                    HEADERS,
            )
    ) or not isinstance(HOMEWORK_STATUSES, dict) \
            or not all(key in HOMEWORK_STATUSES for key in (
            ('approved', 'reviewing', 'rejected'))
                       ):
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
        raise TokenError(TokenError.message)

    # Метка времени для запроса к API
    timestamp = int(time.time())
    # Переменная однократного сообщения об ошибке запроса к API
    notified = False

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

        except APIAccessError:
            logger.warning(APIAccessError.message)
            if not notified:
                send_message(bot, APIAccessError.message)
                notified = True

        finally:
            time.sleep(RETRY_TIME or 600)


if __name__ == '__main__':
    main()
