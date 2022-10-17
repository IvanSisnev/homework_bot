"""
Файл с исключениями для homework.py
"""


class MyException(Exception):
    """
    Родительский класс.
    """
    pass


class TokenError(MyException):
    """
    Класс для обработки ошибки токенов и констант модуля.
    """
    message = 'Не удалось загрузить токены или константы.'


class BotMalfunction(MyException):
    """
    Класс обработки ошибки невозможности отправки сообщений и ошибочной работы
    бота Телеграм.
    """
    message = 'Не удалось отправить сообщение. С ботом что-то не так.'


class APIAccessError(MyException):
    """
    Класс обработки ошибки доступа к URL адреса API.
    """
    message = 'Ошибка доступа к URL адресу API.'


class APIResponseError(MyException):
    """
    Класс обработки ошибки получения данных от API.
    """
    message = 'Некорректные данные от API.'


class DataError(MyException):
    """
    Класс обработки ошибки данных, полученных от API.
    """
    message = 'Ошибка обработки данных, полученных от API.'
