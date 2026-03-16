
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer



from .models import (
    CustomUser, Referral, UserBalance, Transaction, Bonus, ReferralLevel, ReferralBonus
)
from .services import BonusService
from .telegram_utils import extract_user_data


class TelegramLoginSerializer(serializers.Serializer):
    telegramData = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=1000,
        help_text="Telegram initData string"
    )
    referredBy = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of the user who referred the current user"
    )

    def validate(self, attrs):
        telegram_data = attrs["telegramData"]
        referred_by = attrs.get("referredBy")

        if not telegram_data:
            raise serializers.ValidationError("Telegram data is required")

        try:
            # Extract and verify user data
            try:
                user_data = extract_user_data(telegram_data)
            except Exception as e:
                # Для разработки создаем тестового пользователя
                if telegram_data == "test_data":
                    user_data = {
                        'id': 12345,
                        'username': 'test_user',
                        'first_name': 'Test',
                        'last_name': 'User'
                    }
                else:
                    raise serializers.ValidationError(f"Failed to extract Telegram data: {str(e)}")
            
            # Check required fields
            if 'id' not in user_data:
                raise serializers.ValidationError("Invalid user data: missing ID")
            
            telegram_id = str(user_data['id'])
            username = user_data.get('username') or f"tg_{telegram_id}"
            
            # Find existing user by Telegram ID
            telegram_user = CustomUser.objects.filter(telegram_id=telegram_id).first()
            
            if telegram_user is None:
                # Create new user
                referrer_user = None
                if referred_by:
                    try:
                        # Очистка префикса ref_ если есть (из Telegram start параметра)
                        ref_id = str(referred_by)
                        if ref_id.startswith('ref_'):
                            ref_id = ref_id.replace('ref_', '')
                        
                        referrer_user = CustomUser.objects.filter(telegram_id=ref_id).first()
                    except (ValueError, TypeError):
                        # Ignore invalid referrer ID
                        pass

                user = CustomUser.objects.create(
                    username=username,
                    telegram_id=telegram_id,
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    referred_by=referrer_user,
                )
                user.set_password(None)
                
                if referrer_user:
                    Referral.objects.create(referrer=referrer_user, referred=user)
            else:
                # Update existing user
                telegram_user.username = username
                telegram_user.first_name = user_data.get('first_name', '')
                telegram_user.last_name = user_data.get('last_name', '')
                telegram_user.save()
                user = telegram_user

            attrs["user"] = user
            
            # Проверяем ежедневный бонус для всех пользователей при входе
            try:
                created, message, bonus = BonusService.check_daily_login_bonus(user)
                if created and bonus:
                    # Логируем успешное начисление бонуса, но не прерываем процесс авторизации
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Начислен ежедневный бонус пользователю {user.username}: {message}")
            except Exception as e:
                # Не прерываем авторизацию из-за ошибки с бонусом
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка при проверке ежедневного бонуса для {user.username}: {str(e)}")
            
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid Telegram data: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"Authentication failed: {str(e)}")

        return attrs


class CustomUserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("username",)


class UserBalanceSerializer(ModelSerializer):
    class Meta:
        model = UserBalance
        fields = (
            "coins_balance",
            "total_earned",
            "total_spent",
            "updated_at",
        )
        read_only_fields = (
            "coins_balance",
            "total_earned",
            "total_spent",
            "updated_at",
        )


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "amount",
            "type",
            "description",
            "reference_id",
            "created_at",
        )
        read_only_fields = (
            "id",
            "amount",
            "type",
            "description",
            "reference_id",
            "created_at",
        )


class UserInfoSerializer(ModelSerializer):
    balance = UserBalanceSerializer(read_only=True)
    
    class Meta:
        depth = 2
        model = CustomUser
        fields = (
            "id",
            "username",
            "balance",
            "telegram_id",
            "referral_count",
        )
        read_only_fields = (
            "id",
            "username",
            "balance",
            "telegram_id",
            "referral_points",
        )


class BonusSerializer(ModelSerializer):
    """
    Сериализатор для чтения бонусов
    """
    bonus_type_display = serializers.CharField(source='get_bonus_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_be_used = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Bonus
        fields = (
            'id',
            'bonus_type',
            'bonus_type_display',
            'amount',
            'status',
            'status_display',
            'description',
            'expires_at',
            'created_at',
            'used_at',
            'can_be_used',
            'is_expired'
        )
        read_only_fields = (
            'id',
            'bonus_type',
            'amount',
            'status',
            'description',
            'expires_at',
            'created_at',
            'used_at',
        )
    
    def get_can_be_used(self, obj):
        """Проверить можно ли использовать бонус"""
        return obj.can_be_used()
    
    def get_is_expired(self, obj):
        """Проверить истек ли бонус"""
        return obj.is_expired()


class BonusStatisticsSerializer(serializers.Serializer):
    """
    Сериализатор для статистики бонусов
    """
    total_bonuses = serializers.IntegerField(read_only=True)
    used_bonuses = serializers.IntegerField(read_only=True)
    pending_bonuses = serializers.IntegerField(read_only=True)
    active_bonuses = serializers.IntegerField(read_only=True)
    expired_bonuses = serializers.IntegerField(read_only=True)
    total_earned_from_bonuses = serializers.IntegerField(read_only=True)
    bonus_types_stats = serializers.DictField(read_only=True)
    last_bonus = BonusSerializer(read_only=True)


class ClaimDailyBonusSerializer(serializers.Serializer):
    """
    Сериализатор для получения ежедневного бонуса
    """
    pass


class ClaimSocialBonusSerializer(serializers.Serializer):
    """
    Сериализатор для получения бонуса за подписку
    """
    pass


class ReferralLevelSerializer(serializers.ModelSerializer):
    """
    Сериализатор для уровней реферальной программы
    """
    class Meta:
        model = ReferralLevel
        fields = (
            'id',
            'level',
            'min_referrals',
            'bonus_percentage',
            'is_active',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ReferralSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рефералов
    """
    referrer_username = serializers.CharField(source='referrer.username', read_only=True)
    referred_username = serializers.CharField(source='referred.username', read_only=True)
    
    class Meta:
        model = Referral
        fields = (
            'id',
            'referrer',
            'referred',
            'referrer_username',
            'referred_username',
            'approved',
            'total_bonus_earned',
            'last_bonus_at',
            'created_at'
        )
        read_only_fields = ('id', 'total_bonus_earned', 'last_bonus_at', 'created_at')


class ReferralBonusSerializer(serializers.ModelSerializer):
    """
    Сериализатор для истории реферальных бонусов
    """
    referrer_username = serializers.CharField(source='referrer.username', read_only=True)
    referred_username = serializers.CharField(source='referred.username', read_only=True)
    
    class Meta:
        model = ReferralBonus
        fields = (
            'id',
            'referrer',
            'referred',
            'referrer_username',
            'referred_username',
            'investment_amount',
            'bonus_amount',
            'bonus_percentage',
            'referral_level',
            'presale_round',
            'transaction_id',
            'created_at'
        )
        read_only_fields = '__all__'


