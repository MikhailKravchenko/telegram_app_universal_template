import logging
from typing import Optional, Tuple
from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.db.models import Sum, Count, Q
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import CustomUser, UserBalance, Transaction, Bonus, UserActivityHour, BonusSettings, Referral, ReferralLevel, ReferralBonus, BotSettings

from src.config import config

logger = logging.getLogger(__name__)


def metamask_valid(signer_address: str, address: str) -> bool:
    return signer_address.lower() == address.lower()


def is_valid_signature(signature: str, data: str, secret_key: str) -> bool:
    """Validate signature for data"""
    import hmac
    import hashlib
    
    expected_signature = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


def check_admin_role(user: CustomUser) -> bool:
    """Check if user has admin role"""
    return user.is_staff or user.is_superuser


class BalanceService:
    """
    Service for managing user balance and transactions with enhanced validation
    """
    
    @staticmethod
    def get_user_balance(user: CustomUser) -> Optional[UserBalance]:
        """
        Get user balance or create if doesn't exist
        """
        try:
            return user.balance
        except UserBalance.DoesNotExist:
            # Create balance if doesn't exist (for existing users)
            return UserBalance.objects.create(
                user=user,
                coins_balance=0,
                total_earned=0,
                total_spent=0
            )
    
    @staticmethod
    def validate_amount(amount: int, operation: str = "operation") -> None:
        """
        Validate transaction amount
        
        Args:
            amount: Amount to validate
            operation: Operation description for error messages
            
        Raises:
            ValidationError: If amount is invalid
        """
        if not isinstance(amount, int):
            raise ValidationError(f"Amount must be an integer, got {type(amount)}")
        
        if amount == 0:
            raise ValidationError(f"Amount cannot be zero for {operation}")
        
        if amount > 999999:
            raise ValidationError(f"Amount {amount} exceeds maximum limit for {operation}")
    
    @staticmethod
    def validate_positive_amount(amount: int, operation: str = "operation") -> None:
        """
        Validate that amount is positive
        
        Args:
            amount: Amount to validate
            operation: Operation description for error messages
            
        Raises:
            ValidationError: If amount is not positive
        """
        BalanceService.validate_amount(amount, operation)
        if amount < 0:
            raise ValidationError(f"Amount must be positive for {operation}, got {amount}")
    
    @staticmethod
    def check_sufficient_balance(user: CustomUser, amount: int) -> bool:
        """
        Check if user has sufficient balance for deduction
        
        Args:
            user: User to check balance for
            amount: Amount to deduct
            
        Returns:
            bool: True if sufficient balance, False otherwise
        """
        try:
            user_balance = BalanceService.get_user_balance(user)
            return user_balance.coins_balance >= amount
        except Exception as e:
            logger.error(f"Error checking balance for user {user.username}: {str(e)}")
            return False
    
    @staticmethod
    def add_coins(user: CustomUser, amount: int, transaction_type: str, 
                  description: str = "", reference_id: str = None) -> Tuple[bool, str]:
        """
        Add coins to user balance and create transaction record
        
        Args:
            user: User to add coins to
            amount: Amount of coins to add (positive)
            transaction_type: Type of transaction
            description: Transaction description
            reference_id: Reference ID for related object
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate amount
            BalanceService.validate_positive_amount(amount, f"adding coins for {transaction_type}")
            
            # Validate transaction type
            if transaction_type not in ['bonus', 'win', 'referral', 'daily_login', 'social_subscription', 'starting_balance', 'round_participation']:
                raise ValidationError(f"Invalid transaction type '{transaction_type}' for adding coins")
            
            with transaction.atomic():
                # Get or create user balance
                user_balance = BalanceService.get_user_balance(user)
                
                # Update balance
                user_balance.coins_balance += amount
                user_balance.total_earned += amount
                user_balance.save()
                
                # Create transaction record
                Transaction.objects.create(
                    user=user,
                    amount=amount,
                    type=transaction_type,
                    description=description,
                    reference_id=reference_id
                )
                
                logger.info(f"Added {amount} coins to user {user.username} for {transaction_type}")
                return True, f"Successfully added {amount} coins for {transaction_type}"
                
        except ValidationError as e:
            logger.warning(f"Validation error adding coins to user {user.username}: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Failed to add coins to user {user.username}: {str(e)}")
            return False, f"Internal error: {str(e)}"
    
    @staticmethod
    def deduct_coins(user: CustomUser, amount: int, transaction_type: str,
                    description: str = "", reference_id: str = None) -> Tuple[bool, str]:
        """
        Deduct coins from user balance and create transaction record
        
        Args:
            user: User to deduct coins from
            amount: Amount of coins to deduct (positive)
            transaction_type: Type of transaction
            description: Transaction description
            reference_id: Reference ID for related object
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate amount
            BalanceService.validate_positive_amount(amount, f"deducting coins for {transaction_type}")
            
            # Validate transaction type
            if transaction_type not in ['bet', 'transfer', 'presale_investment']:
                raise ValidationError(f"Invalid transaction type '{transaction_type}' for deducting coins")
            
            with transaction.atomic():
                # Get or create user balance
                user_balance = BalanceService.get_user_balance(user)
                
                # Check if user has enough coins
                if user_balance.coins_balance < amount:
                    raise ValidationError(f"Insufficient balance. Required: {amount}, Available: {user_balance.coins_balance}")
                
                # Update balance
                user_balance.coins_balance -= amount
                user_balance.total_spent += amount
                user_balance.save()
                
                # Create transaction record (negative amount)
                Transaction.objects.create(
                    user=user,
                    amount=-amount,
                    type=transaction_type,
                    description=description,
                    reference_id=reference_id
                )
                
                logger.info(f"Deducted {amount} coins from user {user.username} for {transaction_type}")
                return True, f"Successfully deducted {amount} coins for {transaction_type}"
                
        except ValidationError as e:
            logger.warning(f"Validation error deducting coins from user {user.username}: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Failed to deduct coins from user {user.username}: {str(e)}")
            return False, f"Internal error: {str(e)}"
    
    @staticmethod
    def transfer_coins(from_user: CustomUser, to_user: CustomUser, amount: int,
                      description: str = "", reference_id: str = None) -> Tuple[bool, str]:
        """
        Transfer coins between users with enhanced validation
        
        Args:
            from_user: User to deduct coins from
            to_user: User to add coins to
            amount: Amount of coins to transfer
            description: Transaction description
            reference_id: Reference ID for related object
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate amount
            BalanceService.validate_positive_amount(amount, "transfer")
            
            # Validate users
            if from_user == to_user:
                raise ValidationError("Cannot transfer coins to yourself")
            
            if not from_user.is_active or not to_user.is_active:
                raise ValidationError("Both users must be active for transfer")
            
            with transaction.atomic():
                # Deduct from sender
                success, message = BalanceService.deduct_coins(
                    from_user, amount, "transfer", 
                    f"Transfer to {to_user.username}", reference_id
                )
                if not success:
                    return False, f"Failed to deduct from sender: {message}"
                
                # Add to receiver
                success, message = BalanceService.add_coins(
                    to_user, amount, "bonus",
                    f"Transfer from {from_user.username}", reference_id
                )
                if not success:
                    # Rollback sender deduction if receiver addition fails
                    BalanceService.add_coins(
                        from_user, amount, "rollback", 
                        f"Rollback of failed transfer to {to_user.username}"
                    )
                    return False, f"Failed to add to receiver: {message}"
                
                logger.info(f"Transferred {amount} coins from {from_user.username} to {to_user.username}")
                return True, f"Successfully transferred {amount} coins from {from_user.username} to {to_user.username}"
                
        except ValidationError as e:
            logger.warning(f"Validation error in transfer: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Failed to transfer coins between users: {str(e)}")
            return False, f"Internal error: {str(e)}"
    
    @staticmethod
    def get_balance_summary(user: CustomUser) -> dict:
        """
        Get comprehensive balance summary for user
        
        Args:
            user: User to get summary for
            
        Returns:
            dict: Balance summary with statistics
        """
        try:
            user_balance = BalanceService.get_user_balance(user)
            
            # Get recent transactions
            recent_transactions = Transaction.objects.filter(
                user=user
            ).order_by('-created_at')[:10]
            
            # Calculate statistics
            total_transactions = Transaction.objects.filter(user=user).count()
            positive_transactions = Transaction.objects.filter(user=user, amount__gt=0).count()
            negative_transactions = Transaction.objects.filter(user=user, amount__lt=0).count()
            
            return {
                'current_balance': user_balance.coins_balance,
                'total_earned': user_balance.total_earned,
                'total_spent': user_balance.total_spent,
                'net_earnings': user_balance.total_earned - user_balance.total_spent,
                'total_transactions': total_transactions,
                'positive_transactions': positive_transactions,
                'negative_transactions': negative_transactions,
                'last_updated': user_balance.updated_at,
                'recent_transactions': [
                    {
                        'amount': t.amount,
                        'type': t.type,
                        'description': t.description,
                        'created_at': t.created_at
                    } for t in recent_transactions
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance summary for user {user.username}: {str(e)}")
            return {
                'error': f"Failed to get balance summary: {str(e)}"
            }


class BonusService:
    """
    Service for managing user bonuses
    """
    
    @staticmethod
    def create_bonus(user: CustomUser, bonus_type: str, amount: int, 
                    description: str = "", reference_id: str = None,
                    expires_at: Optional[timezone.datetime] = None) -> Tuple[bool, str, Optional[Bonus]]:
        """
        Создать новый бонус для пользователя
        
        Args:
            user: Пользователь
            bonus_type: Тип бонуса
            amount: Сумма бонуса
            description: Описание бонуса
            reference_id: ID связанного объекта
            expires_at: Дата истечения бонуса
            
        Returns:
            Tuple[bool, str, Optional[Bonus]]: (success, message, bonus_object)
        """
        try:
            # Валидация типа бонуса - получаем актуальный список из модели
            valid_types = [choice[0] for choice in Bonus.BONUS_TYPES]
            if bonus_type not in valid_types:
                raise ValidationError(f"Недопустимый тип бонуса: {bonus_type}")
            
            # Валидация суммы
            if amount <= 0:
                raise ValidationError("Сумма бонуса должна быть положительной")
            
            # Создаем бонус
            bonus = Bonus.objects.create(
                user=user,
                bonus_type=bonus_type,
                amount=amount,
                description=description,
                reference_id=reference_id,
                expires_at=expires_at,
                status='pending'
            )
            
            logger.info(f"Создан бонус {bonus_type} на {amount} монет для пользователя {user.username}")
            return True, f"Бонус {bonus_type} успешно создан", bonus
            
        except ValidationError as e:
            logger.warning(f"Ошибка валидации при создании бонуса: {str(e)}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Ошибка при создании бонуса: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}", None
    
    @staticmethod
    def activate_bonus(bonus: Bonus) -> Tuple[bool, str]:
        """
        Активировать бонус
        
        Args:
            bonus: Объект бонуса
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if bonus.status != 'pending':
                raise ValidationError(f"Бонус уже имеет статус {bonus.status}")
            
            if bonus.is_expired():
                bonus.status = 'expired'
                bonus.save()
                raise ValidationError("Бонус истек")
            
            bonus.activate()
            logger.info(f"Активирован бонус {bonus.id} для пользователя {bonus.user.username}")
            return True, "Бонус успешно активирован"
            
        except ValidationError as e:
            logger.warning(f"Ошибка активации бонуса {bonus.id}: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Ошибка при активации бонуса {bonus.id}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}"
    
    @staticmethod
    def use_bonus(bonus: Bonus) -> Tuple[bool, str]:
        """
        Использовать бонус и начислить монеты
        
        Args:
            bonus: Объект бонуса
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not bonus.can_be_used():
                raise ValidationError("Бонус нельзя использовать")
            
            with transaction.atomic():
                bonus.use()
                
                logger.info(f"Использован бонус {bonus.id}, начислено {bonus.amount} монет пользователю {bonus.user.username}")
                return True, f"Бонус использован, начислено {bonus.amount} монет"
            
        except ValidationError as e:
            logger.warning(f"Ошибка использования бонуса {bonus.id}: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Ошибка при использовании бонуса {bonus.id}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}"
    
    @staticmethod
    def check_daily_login_bonus(user: CustomUser) -> Tuple[bool, str, Optional[Bonus]]:
        """
        Проверить и создать ежедневный бонус за вход
        
        Args:
            user: Пользователь
            
        Returns:
            Tuple[bool, str, Optional[Bonus]]: (created, message, bonus_object)
        """
        try:
            # Проверяем, получал ли пользователь бонус сегодня
            today = timezone.now().date()
            existing_bonus = Bonus.objects.filter(
                user=user,
                bonus_type='daily_login',
                created_at__date=today
            ).first()
            
            if existing_bonus:
                return False, "Ежедневный бонус уже получен сегодня", existing_bonus
            
            # Получаем настройки бонусов
            settings = BonusSettings.get_settings()
            
            # Создаем и активируем бонус
            success, message, bonus = BonusService.create_bonus(
                user=user,
                bonus_type='daily_login',
                amount=settings.daily_login_bonus,
                description="Ежедневный бонус за вход"
            )
            
            if success and bonus:
                # Автоматически активируем и используем бонус
                BonusService.activate_bonus(bonus)
                BonusService.use_bonus(bonus)
                
                logger.info(f"Начислен ежедневный бонус {settings.daily_login_bonus} монет пользователю {user.username}")
                return True, f"Получен ежедневный бонус +{settings.daily_login_bonus} монет!", bonus
            
            return False, message, None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке ежедневного бонуса для {user.username}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}", None
    
    @staticmethod
    def check_first_bet_bonus(user: CustomUser, bet_id: str) -> Tuple[bool, str, Optional[Bonus]]:
        """
        Проверить и создать бонус за первую ставку
        
        Args:
            user: Пользователь
            bet_id: ID ставки
            
        Returns:
            Tuple[bool, str, Optional[Bonus]]: (created, message, bonus_object)
        """
        try:
            # Проверяем, получал ли пользователь бонус за первую ставку
            existing_bonus = Bonus.objects.filter(
                user=user,
                bonus_type='first_bet'
            ).first()
            
            if existing_bonus:
                return False, "Бонус за первую ставку уже получен", existing_bonus
            
            # Получаем настройки бонусов
            settings = BonusSettings.get_settings()
            
            # Создаем и активируем бонус
            success, message, bonus = BonusService.create_bonus(
                user=user,
                bonus_type='first_bet',
                amount=settings.first_bet_bonus,
                description="Бонус за первую ставку",
                reference_id=bet_id
            )
            
            if success and bonus:
                # Автоматически активируем и используем бонус
                BonusService.activate_bonus(bonus)
                BonusService.use_bonus(bonus)
                
                logger.info(f"Начислен бонус за первую ставку {settings.first_bet_bonus} монет пользователю {user.username}")
                return True, f"Получен бонус за первую ставку +{settings.first_bet_bonus} монет!", bonus
            
            return False, message, None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке бонуса за первую ставку для {user.username}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}", None
    
    @staticmethod
    def check_round_participation_bonus(user: CustomUser, round_id: int) -> Tuple[bool, str, Optional[Bonus]]:
        """
        Проверить и создать бонус за участие в раунде с учетом новых ограничений
        
        Args:
            user: Пользователь
            round_id: ID раунда
            
        Returns:
            Tuple[bool, str, Optional[Bonus]]: (created, message, bonus_object)
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            # Получаем настройки бонусов
            settings = BonusSettings.get_settings()
            
            # Проверяем количество участий в этом раунде
            round_participations = Bonus.objects.filter(
                user=user,
                bonus_type='round_participation',
                reference_id__startswith=str(round_id) + "_"
            ).count()
            
            if round_participations >= settings.max_participations_per_round:
                return False, f"Превышен лимит участий в раунде ({settings.max_participations_per_round} раз)", None
            
            # Проверяем часовой лимит
            one_hour_ago = timezone.now() - timedelta(hours=1)
            hourly_participations = Bonus.objects.filter(
                user=user,
                bonus_type='round_participation',
                created_at__gte=one_hour_ago
            ).count()
            
            if hourly_participations >= settings.hourly_limit_round_participation:
                return False, f"Превышен часовой лимит участий ({settings.hourly_limit_round_participation} раз в час)", None
            
            # Размер бонуса за участие в раунде из настроек
            bonus_amount = settings.round_participation_bonus
            
            # Создаем уникальный reference_id для каждого участия
            participation_number = round_participations + 1
            unique_reference_id = f"{round_id}_{participation_number}"
            
            # Создаем и активируем бонус
            success, message, bonus = BonusService.create_bonus(
                user=user,
                bonus_type='round_participation',
                amount=bonus_amount,
                description=f"Бонус за участие в раунде {round_id} (попытка {participation_number})",
                reference_id=unique_reference_id
            )
            
            if success and bonus:
                # Автоматически активируем и используем бонус
                BonusService.activate_bonus(bonus)
                BonusService.use_bonus(bonus)
                
                logger.info(f"Начислен бонус за участие в раунде {bonus_amount} монет пользователю {user.username} (попытка {participation_number}/{settings.max_participations_per_round})")
                return True, f"Получен бонус за участие в раунде +{bonus_amount} монет! ({participation_number}/{settings.max_participations_per_round})", bonus
            
            return False, message, None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке бонуса за участие в раунде для {user.username}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}", None
    
    @staticmethod
    def check_social_subscription_bonus(user: CustomUser) -> Tuple[bool, str, Optional[Bonus]]:
        """
        Проверить и создать бонус за подписку на соцсеть
        
        Args:
            user: Пользователь
            
        Returns:
            Tuple[bool, str, Optional[Bonus]]: (created, message, bonus_object)
        """
        try:
            # Проверяем, получал ли пользователь бонус за подписку
            existing_bonus = Bonus.objects.filter(
                user=user,
                bonus_type='social_subscription'
            ).first()
            
            if existing_bonus:
                return False, "Бонус за подписку уже получен", existing_bonus
            
            # Получаем настройки бонусов
            settings = BonusSettings.get_settings()
            
            # Создаем бонус (активация вручную после проверки подписки)
            success, message, bonus = BonusService.create_bonus(
                user=user,
                bonus_type='social_subscription',
                amount=settings.social_subscription_bonus,
                description="Бонус за подписку на соцсеть"
            )
            
            if success and bonus:
                logger.info(f"Создан бонус за подписку {settings.social_subscription_bonus} монет для пользователя {user.username}")
                return True, "Бонус за подписку создан, требуется подтверждение", bonus
            
            return False, message, None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке бонуса за подписку для {user.username}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}", None

    @staticmethod
    def check_telegram_channel_1_bonus(user: CustomUser) -> Tuple[bool, str, Optional[Bonus]]:
        """
        Проверить и создать бонус за подписку на Telegram канал 1
        
        Args:
            user: Пользователь
            
        Returns:
            Tuple[bool, str, Optional[Bonus]]: (created, message, bonus_object)
        """
        try:
            # Проверяем, получал ли пользователь бонус за подписку на канал 1
            existing_bonus = Bonus.objects.filter(
                user=user,
                bonus_type='telegram_channel_1'
            ).first()
            
            if existing_bonus:
                return False, "Бонус за подписку на Telegram канал 1 уже получен", existing_bonus
            
            # Получаем настройки бонусов
            settings = BonusSettings.get_settings()
            
            # Создаем бонус (активация вручную после проверки подписки)
            success, message, bonus = BonusService.create_bonus(
                user=user,
                bonus_type='telegram_channel_1',
                amount=settings.telegram_channel_1_bonus,
                description="Бонус за подписку на Telegram канал 1"
            )
            
            if success and bonus:
                logger.info(f"Создан бонус за подписку на Telegram канал 1 {settings.telegram_channel_1_bonus} монет для пользователя {user.username}")
                return True, "Бонус за подписку на Telegram канал 1 создан, требуется подтверждение", bonus
            
            return False, message, None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке бонуса за подписку на Telegram канал 1 для {user.username}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}", None

    @staticmethod
    def check_telegram_channel_2_bonus(user: CustomUser) -> Tuple[bool, str, Optional[Bonus]]:
        """
        Проверить и создать бонус за подписку на Telegram канал 2
        
        Args:
            user: Пользователь
            
        Returns:
            Tuple[bool, str, Optional[Bonus]]: (created, message, bonus_object)
        """
        try:
            # Проверяем, получал ли пользователь бонус за подписку на канал 2
            existing_bonus = Bonus.objects.filter(
                user=user,
                bonus_type='telegram_channel_2'
            ).first()
            
            if existing_bonus:
                return False, "Бонус за подписку на Telegram канал 2 уже получен", existing_bonus
            
            # Получаем настройки бонусов
            settings = BonusSettings.get_settings()
            
            # Создаем бонус (активация вручную после проверки подписки)
            success, message, bonus = BonusService.create_bonus(
                user=user,
                bonus_type='telegram_channel_2',
                amount=settings.telegram_channel_2_bonus,
                description="Бонус за подписку на Telegram канал 2"
            )
            
            if success and bonus:
                logger.info(f"Создан бонус за подписку на Telegram канал 2 {settings.telegram_channel_2_bonus} монет для пользователя {user.username}")
                return True, "Бонус за подписку на Telegram канал 2 создан, требуется подтверждение", bonus
            
            return False, message, None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке бонуса за подписку на Telegram канал 2 для {user.username}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}", None
    
    @staticmethod
    def get_user_bonuses(user: CustomUser, status: str = None) -> list:
        """
        Получить бонусы пользователя
        
        Args:
            user: Пользователь
            status: Фильтр по статусу (optional)
            
        Returns:
            list: Список бонусов
        """
        try:
            queryset = Bonus.objects.filter(user=user)
            
            if status:
                queryset = queryset.filter(status=status)
            
            return list(queryset.order_by('-created_at'))
            
        except Exception as e:
            logger.error(f"Ошибка при получении бонусов для пользователя {user.username}: {str(e)}")
            return []
    
    @staticmethod
    def get_bonus_statistics(user: CustomUser) -> dict:
        """
        Получить статистику по бонусам пользователя
        
        Args:
            user: Пользователь
            
        Returns:
            dict: Статистика по бонусам
        """
        try:
            bonuses = Bonus.objects.filter(user=user)
            
            total_bonuses = bonuses.count()
            used_bonuses = bonuses.filter(status='used').count()
            pending_bonuses = bonuses.filter(status='pending').count()
            active_bonuses = bonuses.filter(status='active').count()
            expired_bonuses = bonuses.filter(status='expired').count()
            
            total_earned = sum(bonus.amount for bonus in bonuses.filter(status='used'))
            
            # Статистика по типам
            bonus_types_stats = {}
            for bonus_type, _ in Bonus.BONUS_TYPES:
                count = bonuses.filter(bonus_type=bonus_type).count()
                earned = sum(bonus.amount for bonus in bonuses.filter(bonus_type=bonus_type, status='used'))
                bonus_types_stats[bonus_type] = {
                    'count': count,
                    'earned': earned
                }
            
            return {
                'total_bonuses': total_bonuses,
                'used_bonuses': used_bonuses,
                'pending_bonuses': pending_bonuses,
                'active_bonuses': active_bonuses,
                'expired_bonuses': expired_bonuses,
                'total_earned_from_bonuses': total_earned,
                'bonus_types_stats': bonus_types_stats,
                'last_bonus': bonuses.order_by('-created_at').first()
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики бонусов для {user.username}: {str(e)}")
            return {'error': f"Ошибка получения статистики: {str(e)}"}


class ActivityService:
    """
    Сервис для управления активностью пользователей и бонусами за активные ставки
    """
    
    @staticmethod
    def get_current_hour_start() -> timezone.datetime:
        """Получить начало текущего часа"""
        now = timezone.now()
        return now.replace(minute=0, second=0, microsecond=0)
    
    @staticmethod
    def record_bet_activity(user: CustomUser) -> Tuple[bool, str]:
        """
        Зарегистрировать активность ставки пользователя и начислить бонус за активность
        
        Новая логика: бонус начисляется СРАЗУ при каждой ставке, если не превышены дневные лимиты.
        Лимиты считаются по календарным суткам (00:00 - 23:59).
        
        Args:
            user: Пользователь, сделавший ставку
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            hour_start = ActivityService.get_current_hour_start()
            settings = BonusSettings.get_settings()
            
            # Начало текущих календарных суток (00:00)
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            with transaction.atomic():
                # 1. Обновляем статистику (для аналитики)
                activity_hour, created = UserActivityHour.objects.get_or_create(
                    user=user,
                    hour_start=hour_start,
                    defaults={'bets_count': 0}
                )
                
                activity_hour.bets_count += 1
                activity_hour.save(update_fields=['bets_count'])
                
                # 2. Проверяем лимиты для начисления бонуса за активность
                # Считаем сколько activity_bonus получено СЕГОДНЯ (календарные сутки)
                today_activity_bonuses = Bonus.objects.filter(
                    user=user,
                    bonus_type='activity_bonus',
                    created_at__gte=today_start,
                    status='used'  # только использованные (начисленные)
                )
                
                bonuses_count_today = today_activity_bonuses.count()
                total_amount_today = sum(b.amount for b in today_activity_bonuses)
                
                # Проверка лимита по количеству бонусов
                if bonuses_count_today >= settings.activity_max_bets_per_hour:
                    logger.debug(f"Пользователь {user.username} достиг дневного лимита по количеству бонусов ({bonuses_count_today}/{settings.activity_max_bets_per_hour})")
                    return True, f"Ставка зарегистрирована. Дневной лимит бонусов достигнут ({bonuses_count_today}/{settings.activity_max_bets_per_hour})"
                
                # Проверка лимита по сумме
                if total_amount_today + settings.activity_coins_per_bet > settings.activity_daily_limit:
                    logger.debug(f"Пользователь {user.username} достиг дневного лимита по сумме ({total_amount_today + settings.activity_coins_per_bet}/{settings.activity_daily_limit})")
                    return True, f"Ставка зарегистрирована. Дневной лимит суммы бонусов достигнут ({total_amount_today}/{settings.activity_daily_limit})"
                
                # 3. Создаем и начисляем бонус СРАЗУ
                success, message, bonus = BonusService.create_bonus(
                    user=user,
                    bonus_type='activity_bonus',
                    amount=settings.activity_coins_per_bet,
                    description=f"Бонус за активность: ставка #{bonuses_count_today + 1} за {timezone.now().strftime('%Y-%m-%d')}"
                )
                
                if success and bonus:
                    # Автоматически активируем и используем
                    BonusService.activate_bonus(bonus)
                    BonusService.use_bonus(bonus)
                    
                    logger.info(
                        f"Начислен activity bonus {settings.activity_coins_per_bet} монет пользователю {user.username} "
                        f"({bonuses_count_today + 1}/{settings.activity_max_bets_per_hour}, сумма: {total_amount_today + settings.activity_coins_per_bet}/{settings.activity_daily_limit})"
                    )
                    return True, f"Получен бонус за активность +{settings.activity_coins_per_bet} монет ({bonuses_count_today + 1}/{settings.activity_max_bets_per_hour})"
                
                logger.warning(f"Не удалось создать activity bonus для {user.username}: {message}")
                return True, f"Ставка зарегистрирована, но бонус не начислен: {message}"
                
        except Exception as e:
            logger.error(f"Ошибка при регистрации активности ставки для {user.username}: {str(e)}")
            return False, f"Внутренняя ошибка: {str(e)}"
    
    @staticmethod
    def calculate_hourly_activity_bonuses() -> dict:
        """
        [DEPRECATED] Рассчитать и начислить бонусы за активность за предыдущий час
        
        УСТАРЕЛО: С новой версией бонусы начисляются мгновенно при каждой ставке.
        Этот метод больше не используется и оставлен только для обратной совместимости.
        Будет удален в следующей версии.
        
        Выполняется ежечасно через cron
        
        Returns:
            dict: Статистика обработки (всегда пустая)
        """
        logger.warning(
            "calculate_hourly_activity_bonuses() вызван, но метод устарел. "
            "Бонусы теперь начисляются мгновенно при ставке."
        )
        return {
            'hour_processed': timezone.now().isoformat(),
            'bonuses_awarded': 0,
            'total_amount': 0,
            'errors_count': 0,
            'errors': [],
            'deprecated': True,
            'message': 'Activity bonuses are now granted instantly on bet placement'
        }
    
    @staticmethod
    def get_user_activity_stats(user: CustomUser, hours: int = 24) -> dict:
        """
        Получить статистику активности пользователя за последние N часов
        
        Args:
            user: Пользователь
            hours: Количество часов для анализа
            
        Returns:
            dict: Статистика активности
        """
        try:
            current_hour = ActivityService.get_current_hour_start()
            start_time = current_hour - timedelta(hours=hours)
            
            activities = UserActivityHour.objects.filter(
                user=user,
                hour_start__gte=start_time
            ).order_by('-hour_start')
            
            total_bets = sum(activity.bets_count for activity in activities)
            eligible_hours = activities.filter(eligible_for_bonus=True).count()
            bonuses_earned = activities.filter(bonus_awarded=True).count()
            
            # Получаем настройки для расчета лимитов
            settings = BonusSettings.get_settings()
            
            # Подсчитаем потенциальные бонусы за сегодня
            today_start = current_hour.replace(hour=0)
            today_activities = activities.filter(hour_start__gte=today_start)
            today_bonuses = today_activities.filter(bonus_awarded=True).count()
            max_daily_bonuses = 24  # 24 часа * 1 бонус в час максимум
            
            return {
                'period_hours': hours,
                'total_bets': total_bets,
                'eligible_hours': eligible_hours,
                'bonuses_earned': bonuses_earned,
                'today_bonuses': today_bonuses,
                'max_daily_bonuses': max_daily_bonuses,
                'daily_progress_percent': round((today_bonuses / max_daily_bonuses) * 100, 2) if max_daily_bonuses > 0 else 0,
                'activities': [
                    {
                        'hour': activity.hour_start.strftime('%H:00'),
                        'date': activity.hour_start.date().isoformat(),
                        'bets_count': activity.bets_count,
                        'eligible': activity.eligible_for_bonus,
                        'bonus_awarded': activity.bonus_awarded
                    } for activity in activities
                ]
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики активности для {user.username}: {str(e)}")
            return {'error': f"Ошибка получения статистики: {str(e)}"}
    
    @staticmethod
    def cleanup_old_activities(days: int = 7) -> dict:
        """
        Очистить старые записи активности
        
        Args:
            days: Количество дней для хранения
            
        Returns:
            dict: Статистика очистки
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            deleted_count = UserActivityHour.objects.filter(
                hour_start__lt=cutoff_date
            ).count()
            
            UserActivityHour.objects.filter(
                hour_start__lt=cutoff_date
            ).delete()
            
            logger.info(f"Удалено {deleted_count} старых записей активности (старше {days} дней)")
            return {
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка при очистке старых записей активности: {str(e)}")
            return {'error': f"Ошибка очистки: {str(e)}"}


class BotSettingsService:
    """
    Сервис для работы с настройками бота
    """
    
    @staticmethod
    def get_bot_username() -> str:
        """
        Получить имя пользователя Telegram бота
        
        Returns:
            str: Имя пользователя бота (без @)
        """
        return BotSettings.get_value('telegram_bot_username', 'pulse_bot')
    
    @staticmethod
    def get_bot_name() -> str:
        """
        Получить отображаемое имя Telegram бота
        
        Returns:
            str: Отображаемое имя бота
        """
        return BotSettings.get_value('telegram_bot_name', 'Pulse Bot')
    
    @staticmethod
    def get_bot_description() -> str:
        """
        Получить описание Telegram бота
        
        Returns:
            str: Описание бота
        """
        return BotSettings.get_value('telegram_bot_description', 'Официальный бот проекта Pulse')
    
    @staticmethod
    def get_referral_link(user_id: str, use_telegram_id: bool = True) -> str:
        """
        Получить реферальную ссылку для пользователя
        
        Args:
            user_id: ID пользователя (Telegram ID или обычный ID)
            use_telegram_id: Использовать ли Telegram ID
            
        Returns:
            str: Реферальная ссылка
        """
        bot_username = BotSettingsService.get_bot_username()
        return f"https://t.me/{bot_username}?start=ref_{user_id}"


class ReferralService:
    """
    Сервис для управления реферальной программой
    """
    
    @staticmethod
    def get_user_referral_level(user: CustomUser) -> Optional[ReferralLevel]:
        """
        Получить текущий уровень реферальной программы пользователя
        
        Args:
            user: Пользователь
            
        Returns:
            ReferralLevel или None, если уровень не найден
        """
        try:
            # Подсчитать количество одобренных рефералов
            referral_count = Referral.objects.filter(
                referrer=user,
                approved=True
            ).count()
            
            # Найти подходящий уровень (максимальный доступный)
            level = ReferralLevel.objects.filter(
                min_referrals__lte=referral_count,
                is_active=True
            ).order_by('-min_referrals').first()
            
            return level
            
        except Exception as e:
            logger.error(f"Ошибка при получении уровня реферальной программы для {user.username}: {str(e)}")
            return None
    
    @staticmethod
    def get_referral_link(user: CustomUser) -> str:
        """
        Получить реферальную ссылку пользователя
        
        Args:
            user: Пользователь
            
        Returns:
            str: Реферальная ссылка
        """
        # Формируем ссылку на Telegram бота с ID пользователя
        if user.telegram_id:
            return BotSettingsService.get_referral_link(user.telegram_id)
        else:
            return BotSettingsService.get_referral_link(str(user.id))
    
    @staticmethod
    @transaction.atomic
    def process_referral_bonus(
        referrer: CustomUser,
        referred: CustomUser,
        investment_amount: int,
        presale_round: int
    ) -> Tuple[bool, str, Optional[ReferralBonus]]:
        """
        Обработать реферальный бонус при инвестиции реферала
        
        Args:
            referrer: Пользователь-реферер
            referred: Реферал, который сделал инвестицию
            investment_amount: Сумма инвестиции
            presale_round: Раунд пресейла
            
        Returns:
            Tuple[bool, str, Optional[ReferralBonus]]: (success, message, bonus)
        """
        try:
            # Проверить, что связь реферала существует и одобрена
            referral = Referral.objects.filter(
                referrer=referrer,
                referred=referred,
                approved=True
            ).first()
            
            if not referral:
                return False, "Связь реферала не найдена или не одобрена", None
            
            # Получить текущий уровень реферальной программы
            level = ReferralService.get_user_referral_level(referrer)
            if not level:
                return False, "Уровень реферальной программы не найден", None
            
            # Рассчитать бонус
            bonus_amount = int((investment_amount * level.bonus_percentage) / 100)
            
            if bonus_amount <= 0:
                return False, "Размер бонуса равен нулю", None
            
            # Начислить бонус рефереру
            success, message = BalanceService.add_coins(
                user=referrer,
                amount=bonus_amount,
                transaction_type='referral_bonus',
                description=f'Реферальный бонус за инвестицию {referred.username} в раунде {presale_round}'
            )
            
            if not success:
                return False, f"Ошибка начисления бонуса: {message}", None
            
            # Создать запись о бонусе
            referral_bonus = ReferralBonus.objects.create(
                referrer=referrer,
                referred=referred,
                investment_amount=investment_amount,
                bonus_amount=bonus_amount,
                bonus_percentage=level.bonus_percentage,
                referral_level=level.level,
                presale_round=presale_round,
                transaction_id=message  # BalanceService возвращает ID транзакции в message при успехе
            )
            
            # Обновить статистику реферала
            referral.total_bonus_earned += bonus_amount
            referral.last_bonus_at = timezone.now()
            referral.save()
            
            logger.info(
                f"Начислен реферальный бонус {bonus_amount} монет пользователю {referrer.username} "
                f"за инвестицию {referred.username} на сумму {investment_amount} монет"
            )
            
            return True, f"Бонус {bonus_amount} монет начислен", referral_bonus
            
        except Exception as e:
            logger.error(f"Ошибка при обработке реферального бонуса: {str(e)}")
            return False, f"Ошибка обработки бонуса: {str(e)}", None
    
    @staticmethod
    def get_referral_stats(user: CustomUser) -> dict:
        """
        Получить статистику реферальной программы для пользователя
        
        Args:
            user: Пользователь
            
        Returns:
            dict: Статистика реферальной программы
        """
        try:
            # Основная статистика рефералов
            referrals = Referral.objects.filter(referrer=user, approved=True)
            referrals_count = referrals.count()
            
            # Общая сумма бонусов
            total_bonuses = sum(ref.total_bonus_earned for ref in referrals)
            
            # Текущий уровень
            current_level = ReferralService.get_user_referral_level(user)
            
            # Следующий уровень
            next_level = None
            if current_level:
                next_level = ReferralLevel.objects.filter(
                    min_referrals__gt=referrals_count,
                    is_active=True
                ).order_by('min_referrals').first()
            else:
                next_level = ReferralLevel.objects.filter(
                    is_active=True
                ).order_by('min_referrals').first()
            
            # История бонусов (последние 10)
            recent_bonuses = ReferralBonus.objects.filter(
                referrer=user
            ).order_by('-created_at')[:10]
            
            # Статистика по рефералам
            referrals_data = []
            for referral in referrals:
                referrals_data.append({
                    'user_id': referral.referred.id,
                    'username': referral.referred.username,
                    'joined_at': referral.created_at.isoformat(),
                    'total_bonus_earned': referral.total_bonus_earned,
                    'last_bonus_at': referral.last_bonus_at.isoformat() if referral.last_bonus_at else None
                })
            
            # Получаем реферальную ссылку с обработкой ошибок
            try:
                referral_link = ReferralService.get_referral_link(user)
            except Exception as link_error:
                logger.error(f"Ошибка при получении реферальной ссылки: {str(link_error)}")
                referral_link = ""
            
            return {
                'referrals_count': referrals_count,
                'total_bonuses_earned': total_bonuses,
                'referral_link': referral_link,
                'current_level': {
                    'level': current_level.level if current_level else 0,
                    'min_referrals': current_level.min_referrals if current_level else 0,
                    'bonus_percentage': float(current_level.bonus_percentage) if current_level else 0.0,
                    'name': str(current_level) if current_level else "Без уровня"
                } if current_level else None,
                'next_level': {
                    'level': next_level.level if next_level else None,
                    'min_referrals': next_level.min_referrals if next_level else None,
                    'bonus_percentage': float(next_level.bonus_percentage) if next_level else None,
                    'referrals_needed': (next_level.min_referrals - referrals_count) if next_level else 0
                } if next_level else None,
                'recent_bonuses': [
                    {
                        'amount': bonus.bonus_amount,
                        'percentage': float(bonus.bonus_percentage),
                        'investment_amount': bonus.investment_amount,
                        'referred_username': bonus.referred.username,
                        'presale_round': bonus.presale_round,
                        'created_at': bonus.created_at.isoformat()
                    } for bonus in recent_bonuses
                ],
                'referrals': referrals_data
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики рефералов для {user.username}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {'error': f"Ошибка получения статистики: {str(e)}"}
    
    @staticmethod
    def get_global_referral_stats() -> dict:
        """
        Получить глобальную статистику реферальной программы
        
        Returns:
            dict: Глобальная статистика
        """
        try:
            # Общее количество рефералов
            total_referrals = Referral.objects.filter(approved=True).count()
            
            # Общее количество бонусов
            total_bonuses = ReferralBonus.objects.aggregate(
                total_amount=Sum('bonus_amount'),
                total_count=Count('id')
            )
            
            # Топ рефереров
            top_referrers = CustomUser.objects.annotate(
                referrals_count=Count('given_referrals', filter=Q(given_referrals__approved=True)),
                total_bonuses=Sum('referral_bonuses_received__bonus_amount')
            ).filter(referrals_count__gt=0).order_by('-referrals_count')[:10]
            
            # Распределение по уровням
            levels_stats = []
            for level in ReferralLevel.objects.filter(is_active=True).order_by('level'):
                users_at_level = CustomUser.objects.annotate(
                    referrals_count=Count('given_referrals', filter=Q(given_referrals__approved=True))
                ).filter(referrals_count__gte=level.min_referrals).count()
                
                # Если есть следующий уровень, исключаем пользователей с него
                next_level = ReferralLevel.objects.filter(
                    min_referrals__gt=level.min_referrals,
                    is_active=True
                ).order_by('min_referrals').first()
                
                if next_level:
                    users_above = CustomUser.objects.annotate(
                        referrals_count=Count('given_referrals', filter=Q(given_referrals__approved=True))
                    ).filter(referrals_count__gte=next_level.min_referrals).count()
                    users_at_level -= users_above
                
                levels_stats.append({
                    'level': level.level,
                    'min_referrals': level.min_referrals,
                    'bonus_percentage': float(level.bonus_percentage),
                    'users_count': users_at_level
                })
            
            return {
                'total_referrals': total_referrals,
                'total_bonuses_amount': total_bonuses['total_amount'] or 0,
                'total_bonuses_count': total_bonuses['total_count'] or 0,
                'top_referrers': [
                    {
                        'user_id': user.id,
                        'username': user.username,
                        'referrals_count': user.referrals_count,
                        'total_bonuses': user.total_bonuses or 0
                    } for user in top_referrers
                ],
                'levels_distribution': levels_stats
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении глобальной статистики рефералов: {str(e)}")
            return {'error': f"Ошибка получения статистики: {str(e)}"}
    
    @staticmethod
    def create_default_levels() -> dict:
        """
        Создать дефолтные уровни реферальной программы
        
        Returns:
            dict: Результат создания
        """
        try:
            default_levels = [
                {'level': 1, 'min_referrals': 10, 'bonus_percentage': Decimal('5.00')},
                {'level': 2, 'min_referrals': 25, 'bonus_percentage': Decimal('10.00')},
                {'level': 3, 'min_referrals': 50, 'bonus_percentage': Decimal('15.00')},
                {'level': 4, 'min_referrals': 100, 'bonus_percentage': Decimal('20.00')},
                {'level': 5, 'min_referrals': 250, 'bonus_percentage': Decimal('25.00')},
            ]
            
            created_count = 0
            for level_data in default_levels:
                level, created = ReferralLevel.objects.get_or_create(
                    level=level_data['level'],
                    defaults={
                        'min_referrals': level_data['min_referrals'],
                        'bonus_percentage': level_data['bonus_percentage']
                    }
                )
                if created:
                    created_count += 1
                    logger.info(f"Создан уровень {level}")
            
            return {
                'created_count': created_count,
                'total_levels': len(default_levels),
                'message': f"Создано {created_count} новых уровней из {len(default_levels)}"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании дефолтных уровней: {str(e)}")
            return {'error': f"Ошибка создания уровней: {str(e)}"}
    
    @staticmethod
    def approve_referral(referrer_id: int, referred_id: int) -> Tuple[bool, str]:
        """
        Одобрить реферала (если нужно ручное одобрение)
        
        Args:
            referrer_id: ID реферера
            referred_id: ID реферала
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            referral = Referral.objects.get(
                referrer_id=referrer_id,
                referred_id=referred_id
            )
            
            if referral.approved:
                return False, "Реферал уже одобрен"
            
            referral.approved = True
            referral.save()
            
            logger.info(f"Реферал одобрен: {referral}")
            return True, "Реферал успешно одобрен"
            
        except Referral.DoesNotExist:
            return False, "Реферал не найден"
        except Exception as e:
            logger.error(f"Ошибка при одобрении реферала: {str(e)}")
            return False, f"Ошибка одобрения: {str(e)}"
