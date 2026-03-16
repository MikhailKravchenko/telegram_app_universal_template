import logging
from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Tuple, Optional

from django.db import models
from .models import Presale, PresaleRound, Investment, UserPresaleStats
from src.accounts.services import BalanceService

User = get_user_model()
logger = logging.getLogger(__name__)


class PresaleService:
    """Сервис для управления пресейлом"""
    
    @staticmethod
    def get_active_presale() -> Optional[Presale]:
        """Получить активный пресейл"""
        return Presale.objects.filter(status='active').first()
    
    @staticmethod
    def create_presale(name: str = "PULSE Token Presale") -> Presale:
        """Создать новый пресейл"""
        return Presale.objects.create(name=name)
    
    @staticmethod
    def get_current_round_info(presale: Presale) -> dict:
        """Получить информацию о текущем раунде"""
        try:
            round_obj = PresaleRound.objects.get(round_number=presale.current_round)
            return {
                'round_number': presale.current_round,
                'tokens_per_coin': round_obj.tokens_per_coin,
                'target_investment': round_obj.target_investment,
                'max_user_investment': round_obj.max_user_investment,
                'current_investment': presale.current_round_investment,
                'progress_percent': presale.progress_percent,
                'remaining_investment': max(0, round_obj.target_investment - presale.current_round_investment),
                'is_completed': presale.current_round_investment >= round_obj.target_investment,
            }
        except PresaleRound.DoesNotExist:
            return {
                'round_number': presale.current_round,
                'tokens_per_coin': None,
                'target_investment': 0,
                'max_user_investment': 0,
                'current_investment': 0,
                'progress_percent': 0,
                'remaining_investment': 0,
                'is_completed': False,
            }
    
    @staticmethod
    def advance_to_next_round(presale: Presale) -> bool:
        """Перейти к следующему раунду"""
        if presale.current_round >= presale.total_rounds:
            presale.status = 'completed'
            presale.end_time = timezone.now()
            presale.save()
            return False
        
        presale.current_round += 1
        presale.save()
        return True
    
    @staticmethod
    def get_presale_summary(presale: Presale) -> dict:
        """Получить сводку по пресейлу"""
        return {
            'id': presale.id,
            'name': presale.name,
            'status': presale.status,
            'current_round': presale.current_round,
            'total_rounds': presale.total_rounds,
            'total_invested': presale.total_invested,
            'total_tokens_sold': presale.total_tokens_sold,
            'start_time': presale.start_time,
            'end_time': presale.end_time,
            'current_round_info': PresaleService.get_current_round_info(presale),
        }


class InvestmentService:
    """Сервис для управления инвестициями"""
    
    @staticmethod
    def calculate_tokens(amount: int, tokens_per_coin: Decimal) -> Decimal:
        """Рассчитать количество токенов за данную сумму монет"""
        if tokens_per_coin <= 0:
            raise ValidationError("Курс должен быть больше нуля")
        
        tokens = Decimal(amount) * tokens_per_coin
        # Округляем до 2 знаков после запятой
        return tokens.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    @staticmethod
    @transaction.atomic
    def make_investment(
        user: User, 
        presale: Presale, 
        amount: int
    ) -> Tuple[bool, str, Optional[Investment]]:
        """
        Создать инвестицию
        
        Returns:
            Tuple[bool, str, Optional[Investment]]: (success, message, investment)
        """
        # Валидация
        if not presale.is_active():
            return False, "Пресейл не активен", None
        
        if amount <= 0:
            return False, "Сумма инвестиции должна быть больше нуля", None
        
        # Проверить баланс пользователя
        from src.accounts.models import UserBalance
        try:
            user_balance = UserBalance.objects.get(user=user)
            if user_balance.coins_balance < amount:
                return False, f"Недостаточно монет. Доступно: {user_balance.coins_balance}", None
        except UserBalance.DoesNotExist:
            return False, "Баланс пользователя не найден", None
        
        # Получить настройки текущего раунда
        try:
            round_obj = PresaleRound.objects.get(round_number=presale.current_round)
            tokens_per_coin = round_obj.tokens_per_coin
            max_user_investment = round_obj.max_user_investment
        except PresaleRound.DoesNotExist:
            return False, f"Раунд {presale.current_round} не настроен", None
        
        # Проверить лимит пользователя для раунда
        if max_user_investment > 0:
            user_round_investments = Investment.objects.filter(
                user=user,
                presale=presale,
                round_number=presale.current_round
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            if user_round_investments + amount > max_user_investment:
                return False, f"Превышен лимит инвестиций для раунда ({max_user_investment} монет)", None
        
        # Рассчитать токены
        try:
            tokens_received = InvestmentService.calculate_tokens(amount, tokens_per_coin)
        except ValidationError as e:
            return False, str(e), None
        
        # Списать монеты с баланса
        success, message = BalanceService.deduct_coins(
            user=user,
            amount=amount,
            transaction_type='presale_investment',
            description=f'Инвестиция в пресейл раунд {presale.current_round}'
        )
        
        if not success:
            return False, message, None
        
        # Создать инвестицию
        investment = Investment.objects.create(
            user=user,
            presale=presale,
            amount=amount,
            tokens_received=tokens_received,
            round_number=presale.current_round,
            rate_at_purchase=tokens_per_coin,
        )
        
        # Обработать реферальный бонус, если пользователь был приглашен
        if hasattr(user, 'referred_by') and user.referred_by:
            try:
                from src.accounts.services import ReferralService
                success, message, referral_bonus = ReferralService.process_referral_bonus(
                    referrer=user.referred_by,
                    referred=user,
                    investment_amount=amount,
                    presale_round=presale.current_round
                )
                
                if success:
                    logger.info(f"Реферальный бонус обработан: {message}")
                else:
                    logger.warning(f"Не удалось начислить реферальный бонус: {message}")
                    
            except Exception as e:
                logger.error(f"Ошибка при обработке реферального бонуса: {str(e)}")
        
        return True, "Инвестиция успешно создана", investment
    
    @staticmethod
    def get_user_investments(user: User, presale: Optional[Presale] = None) -> list:
        """Получить инвестиции пользователя"""
        investments = Investment.objects.filter(user=user)
        if presale:
            investments = investments.filter(presale=presale)
        
        return investments.order_by('-created_at')
    
    @staticmethod
    def get_user_investment_summary(user: User, presale: Optional[Presale] = None) -> dict:
        """Получить сводку по инвестициям пользователя"""
        investments = InvestmentService.get_user_investments(user, presale)
        
        if not investments.exists():
            return {
                'total_invested': 0,
                'total_tokens': Decimal('0.00'),
                'investments_count': 0,
                'average_rate': Decimal('0.00'),
                'first_investment': None,
                'last_investment': None,
            }
        
        total_invested = sum(inv.amount for inv in investments)
        total_tokens = sum(inv.tokens_received for inv in investments)
        investments_count = len(investments)
        average_rate = Decimal(total_invested) / total_tokens if total_tokens > 0 else Decimal('0.00')
        
        return {
            'total_invested': total_invested,
            'total_tokens': total_tokens,
            'investments_count': investments_count,
            'average_rate': average_rate.quantize(Decimal('0.01')),
            'first_investment': investments.last(),
            'last_investment': investments.first(),
        }


class PresaleRoundService:
    """Сервис для управления раундами пресейла"""
    
    @staticmethod
    def create_default_rounds():
        """Создать дефолтные раунды пресейла (25 раундов с падающим курсом)"""
        default_rounds = [
            # Раунды 1-5: высокий курс (100-80 токенов за монету)
            {'round_number': 1, 'tokens_per_coin': Decimal('100.00'), 'target_investment': 5000, 'max_user_investment': 1000},
            {'round_number': 2, 'tokens_per_coin': Decimal('95.00'), 'target_investment': 7000, 'max_user_investment': 1200},
            {'round_number': 3, 'tokens_per_coin': Decimal('90.00'), 'target_investment': 9000, 'max_user_investment': 1500},
            {'round_number': 4, 'tokens_per_coin': Decimal('85.00'), 'target_investment': 11000, 'max_user_investment': 2000},
            {'round_number': 5, 'tokens_per_coin': Decimal('80.00'), 'target_investment': 13000, 'max_user_investment': 2500},
            
            # Раунды 6-10: средний курс (75-55 токенов за монету)
            {'round_number': 6, 'tokens_per_coin': Decimal('75.00'), 'target_investment': 15000, 'max_user_investment': 3000},
            {'round_number': 7, 'tokens_per_coin': Decimal('70.00'), 'target_investment': 17000, 'max_user_investment': 3500},
            {'round_number': 8, 'tokens_per_coin': Decimal('65.00'), 'target_investment': 19000, 'max_user_investment': 4000},
            {'round_number': 9, 'tokens_per_coin': Decimal('60.00'), 'target_investment': 21000, 'max_user_investment': 4500},
            {'round_number': 10, 'tokens_per_coin': Decimal('55.00'), 'target_investment': 23000, 'max_user_investment': 5000},
            
            # Раунды 11-15: ниже среднего (50-30 токенов за монету)
            {'round_number': 11, 'tokens_per_coin': Decimal('50.00'), 'target_investment': 25000, 'max_user_investment': 5500},
            {'round_number': 12, 'tokens_per_coin': Decimal('45.00'), 'target_investment': 27000, 'max_user_investment': 6000},
            {'round_number': 13, 'tokens_per_coin': Decimal('40.00'), 'target_investment': 29000, 'max_user_investment': 6500},
            {'round_number': 14, 'tokens_per_coin': Decimal('35.00'), 'target_investment': 31000, 'max_user_investment': 7000},
            {'round_number': 15, 'tokens_per_coin': Decimal('30.00'), 'target_investment': 33000, 'max_user_investment': 7500},
            
            # Раунды 16-20: низкий курс (25-10 токенов за монету)
            {'round_number': 16, 'tokens_per_coin': Decimal('25.00'), 'target_investment': 35000, 'max_user_investment': 8000},
            {'round_number': 17, 'tokens_per_coin': Decimal('22.00'), 'target_investment': 37000, 'max_user_investment': 8500},
            {'round_number': 18, 'tokens_per_coin': Decimal('19.00'), 'target_investment': 39000, 'max_user_investment': 9000},
            {'round_number': 19, 'tokens_per_coin': Decimal('16.00'), 'target_investment': 41000, 'max_user_investment': 9500},
            {'round_number': 20, 'tokens_per_coin': Decimal('13.00'), 'target_investment': 43000, 'max_user_investment': 10000},
            
            # Раунды 21-25: очень низкий курс (10-5 токенов за монету)
            {'round_number': 21, 'tokens_per_coin': Decimal('10.00'), 'target_investment': 45000, 'max_user_investment': 10500},
            {'round_number': 22, 'tokens_per_coin': Decimal('8.50'), 'target_investment': 47000, 'max_user_investment': 11000},
            {'round_number': 23, 'tokens_per_coin': Decimal('7.00'), 'target_investment': 49000, 'max_user_investment': 11500},
            {'round_number': 24, 'tokens_per_coin': Decimal('6.00'), 'target_investment': 51000, 'max_user_investment': 12000},
            {'round_number': 25, 'tokens_per_coin': Decimal('5.00'), 'target_investment': 53000, 'max_user_investment': 12500},
        ]
        
        created_rounds = []
        for round_data in default_rounds:
            round_obj, created = PresaleRound.objects.get_or_create(
                round_number=round_data['round_number'],
                defaults={
                    'tokens_per_coin': round_data['tokens_per_coin'],
                    'target_investment': round_data['target_investment'],
                    'max_user_investment': round_data['max_user_investment'],
                }
            )
            if created:
                created_rounds.append(round_obj)
        
        return created_rounds
    
    @staticmethod
    def get_round_info(round_number: int) -> Optional[dict]:
        """Получить информацию о раунде"""
        try:
            round_obj = PresaleRound.objects.get(round_number=round_number)
            return {
                'round_number': round_obj.round_number,
                'tokens_per_coin': round_obj.tokens_per_coin,
                'target_investment': round_obj.target_investment,
                'max_user_investment': round_obj.max_user_investment,
                'is_active': round_obj.is_active,
            }
        except PresaleRound.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_rounds() -> list:
        """Получить все раунды"""
        return list(PresaleRound.objects.all().order_by('round_number'))


class PresaleStatsService:
    """Сервис для статистики пресейла"""
    
    @staticmethod
    def get_global_stats() -> dict:
        """Получить глобальную статистику"""
        from django.db.models import Sum, Count, Avg
        
        presales = Presale.objects.all()
        investments = Investment.objects.all()
        
        return {
            'total_presales': presales.count(),
            'active_presales': presales.filter(status='active').count(),
            'total_investments': investments.count(),
            'total_invested': investments.aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_tokens_sold': investments.aggregate(Sum('tokens_received'))['tokens_received__sum'] or Decimal('0.00'),
            'average_investment': investments.aggregate(Avg('amount'))['amount__avg'] or 0,
            'unique_investors': investments.values('user').distinct().count(),
        }
    
    @staticmethod
    def get_round_stats(presale: Presale) -> list:
        """Получить статистику по раундам для конкретного пресейла"""
        from django.db.models import Sum, Count
        
        rounds_data = []
        for round_number in range(1, presale.total_rounds + 1):
            round_investments = Investment.objects.filter(
                presale=presale,
                round_number=round_number
            )
            
            round_stats = round_investments.aggregate(
                total_invested=Sum('amount'),
                total_tokens=Sum('tokens_received'),
                investors_count=Count('user', distinct=True)
            )
            
            try:
                round_obj = PresaleRound.objects.get(round_number=round_number)
                target = round_obj.target_investment
                rate = round_obj.tokens_per_coin
            except PresaleRound.DoesNotExist:
                target = 0
                rate = None
            
            total_invested = round_stats['total_invested'] or 0
            
            rounds_data.append({
                'round_number': round_number,
                'total_invested': total_invested,
                'total_tokens': round_stats['total_tokens'] or Decimal('0.00'),
                'investors_count': round_stats['investors_count'] or 0,
                'target_investment': target,
                'progress_percent': (total_invested / target * 100) if target > 0 else 0,
                'rate': rate,
                'is_current': round_number == presale.current_round,
                'is_completed': total_invested >= target if target > 0 else False,
            })
        
        return rounds_data
