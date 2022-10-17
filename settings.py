"""
Файл с константами и настройками для homework.py.
"""

import os
# from typing import Final

from dotenv import load_dotenv

load_dotenv()

# Персональный токен пользователя Яндекс.Практикум
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')

# Токен бота Телеграм
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# ID чата для отправки сообщений
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# URL запроса (эндпоинт API)
ENDPOINT: str = ('https://practicum.yandex.ru/api/user_api'
                   '/homework_statuses/')

# Авторизационная информация для запроса к API
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

# Время в секундах между запросами к API
RETRY_TIME: int = 600

# Словарь со статусами проверки работ
HOMEWORK_STATUSES: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

# Кодировка для лог-файла
ENCODING: str = 'UTF-8'
