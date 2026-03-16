import hashlib
import hmac
import os
from urllib.parse import parse_qs, urlparse
from typing import Dict, Any
from src.config import config

from django.conf import settings


def parse_telegram_data(telegram_data: str) -> Dict[str, Any]:
    """
    Парсит данные Telegram из строки initData
    """
    # Декодируем URL-encoded строку
    decoded_data = parse_qs(telegram_data)
    
    # Преобразуем в плоский словарь
    result = {}
    for key, values in decoded_data.items():
        if values:
            result[key] = values[0]
    
    return result


def verify_telegram_data(auth_data: Dict[str, Any]) -> bool:
    """
    Верифицирует данные Telegram используя HMAC-SHA256
    """
    if 'hash' not in auth_data:
        return False
    
    # Получаем токен бота из настроек
    bot_token = config.TELEGRAM_BOT_TOKEN
    if not bot_token:
        return False
    
    # Создаем секретный ключ
    secret_key = hmac.new(
        b'WebAppData',
        bot_token.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Создаем строку для проверки
    check_string = '\n'.join([
        f"{key}={auth_data[key]}"
        for key in sorted(auth_data.keys())
        if key != 'hash'
    ])
    
    # Вычисляем хеш
    computed_hash = hmac.new(
        secret_key,
        check_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return auth_data['hash'] == computed_hash


def extract_user_data(telegram_data: str) -> Dict[str, Any]:
    """
    Извлекает данные пользователя из telegramData
    """
    parsed_data = parse_telegram_data(telegram_data)
    
    if not verify_telegram_data(parsed_data):
        raise ValueError("Invalid Telegram data signature")
    
    if 'user' not in parsed_data:
        raise ValueError("User data not found in Telegram data")
    
    try:
        import json
        user_data = json.loads(parsed_data['user'])
        return user_data
    except (json.JSONDecodeError, KeyError):
        raise ValueError("Invalid user data format")
