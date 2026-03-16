from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login

from .models import CustomUser


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор для получения JWT токенов
    """
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Добавляем дополнительную информацию о пользователе
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'telegram_id': user.telegram_id,
            'email': user.email,
            'is_active': user.is_active,
        }
        
        # Обновляем время последнего входа
        update_last_login(None, user)
        
        return data


class TelegramJWTSerializer(serializers.Serializer):
    """
    Сериализатор для Telegram аутентификации с JWT
    """
    telegramData = serializers.CharField(required=True)
    
    def validate_telegramData(self, value):
        # Здесь должна быть логика валидации Telegram данных
        # Это упрощенная версия, в реальности нужно добавить проверку подписи
        return value
    
    def create(self, validated_data):
        telegram_data = validated_data['telegramData']
        
        # Здесь должна быть логика создания/получения пользователя из Telegram данных
        # Это упрощенная версия
        user, created = CustomUser.objects.get_or_create(
            telegram_id=telegram_data.get('id'),
            defaults={
                'username': f"tg_{telegram_data.get('id')}",
                'first_name': telegram_data.get('first_name', ''),
                'last_name': telegram_data.get('last_name', ''),
            }
        )
        
        # Генерируем JWT токены
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        return {
            'user': user,
            'access': str(access),
            'refresh': str(refresh),
        }


class RefreshTokenSerializer(serializers.Serializer):
    """
    Сериализатор для обновления JWT токенов
    """
    refresh = serializers.CharField(required=True)
    
    def validate_refresh(self, value):
        try:
            RefreshToken(value)
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Invalid refresh token: {str(e)}")


class UserJWTSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователя в JWT ответах
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'telegram_id', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id', 'is_active']
