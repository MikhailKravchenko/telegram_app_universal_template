from datetime import datetime, timedelta
from typing import Optional, Tuple
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()


def create_jwt_tokens(user) -> Tuple[str, str]:
    """
    Создает пару JWT токенов для пользователя
    
    Args:
        user: Пользователь Django
        
    Returns:
        Tuple[str, str]: (access_token, refresh_token)
    """
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    
    return str(access), str(refresh)


def validate_jwt_token(token: str) -> Optional[User]:
    """
    Валидирует JWT токен и возвращает пользователя
    
    Args:
        token: JWT токен
        
    Returns:
        Optional[User]: Пользователь или None если токен невалиден
    """
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id, is_active=True)
        return user
    except (InvalidToken, TokenError, User.DoesNotExist):
        return None


def refresh_jwt_token(refresh_token: str) -> Optional[Tuple[str, str]]:
    """
    Обновляет JWT токен используя refresh токен
    
    Args:
        refresh_token: Refresh токен
        
    Returns:
        Optional[Tuple[str, str]]: (new_access_token, new_refresh_token) или None
    """
    try:
        refresh = RefreshToken(refresh_token)
        new_access = refresh.access_token
        new_refresh = refresh
        
        return str(new_access), str(new_refresh)
    except (InvalidToken, TokenError):
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Получает время истечения JWT токена
    
    Args:
        token: JWT токен
        
    Returns:
        Optional[datetime]: Время истечения или None
    """
    try:
        access_token = AccessToken(token)
        exp_timestamp = access_token['exp']
        return datetime.fromtimestamp(exp_timestamp)
    except (InvalidToken, TokenError):
        return None


def is_token_expired(token: str) -> bool:
    """
    Проверяет, истек ли JWT токен
    
    Args:
        token: JWT токен
        
    Returns:
        bool: True если токен истек, False если нет
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return True
    
    return datetime.now() > expiry


def get_user_from_token(token: str) -> Optional[User]:
    """
    Получает пользователя из JWT токена
    
    Args:
        token: JWT токен
        
    Returns:
        Optional[User]: Пользователь или None
    """
    return validate_jwt_token(token)


def create_custom_jwt_payload(user) -> dict:
    """
    Создает кастомный payload для JWT токена
    
    Args:
        user: Пользователь Django
        
    Returns:
        dict: Кастомный payload
    """
    refresh = RefreshToken.for_user(user)
    
    # Добавляем кастомные claims
    refresh['username'] = user.username
    refresh['telegram_id'] = user.telegram_id
    refresh['email'] = user.email
    
    access = refresh.access_token
    access['username'] = user.username
    access['telegram_id'] = user.telegram_id
    access['email'] = user.email
    
    return {
        'access': str(access),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'telegram_id': user.telegram_id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    }
