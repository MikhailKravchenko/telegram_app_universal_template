import logging
from datetime import timedelta

from django.db.models import Q
from django.utils.timezone import now
from dramatiq import actor

from src.accounts.models import CustomUser, Bonus
from src.accounts.services import BonusService, ActivityService
from src.config import config

logger = logging.getLogger(__name__)


@actor
def expire_bonuses() -> None:
    """
    Задача для истечения просроченных бонусов
    Запускается каждый час
    """
    try:
        # Находим бонусы, которые истекли
        expired_bonuses = Bonus.objects.filter(
            Q(status='pending') | Q(status='active'),
            expires_at__lt=now()
        )
        
        count = expired_bonuses.count()
        if count > 0:
            # Обновляем статус на 'expired'
            expired_bonuses.update(status='expired')
            logger.info(f"Истекло {count} бонусов")
        
    except Exception as e:
        logger.error(f"Ошибка при истечении бонусов: {str(e)}")


@actor 
def cleanup_old_bonuses() -> None:
    """
    Задача для очистки старых использованных/истекших бонусов
    Запускается раз в день, удаляет бонусы старше 30 дней
    """
    try:
        cutoff_date = now() - timedelta(days=30)
        
        # Удаляем старые использованные и истекшие бонусы
        deleted_bonuses = Bonus.objects.filter(
            Q(status='used') | Q(status='expired'),
            created_at__lt=cutoff_date
        )
        
        count = deleted_bonuses.count()
        if count > 0:
            deleted_bonuses.delete()
            logger.info(f"Удалено {count} старых бонусов")
            
    except Exception as e:
        logger.error(f"Ошибка при очистке старых бонусов: {str(e)}")


@actor
def auto_activate_daily_bonuses() -> None:
    """
    Задача для автоматической активации ежедневных бонусов
    Запускается каждые 30 минут
    """
    try:
        # Находим неактивированные ежедневные бонусы
        pending_daily_bonuses = Bonus.objects.filter(
            status='pending',
            bonus_type='daily_login'
        )
        
        activated_count = 0
        for bonus in pending_daily_bonuses:
            if not bonus.is_expired():
                success, message = BonusService.activate_bonus(bonus)
                if success:
                    activated_count += 1
        
        if activated_count > 0:
            logger.info(f"Автоматически активировано {activated_count} ежедневных бонусов")
            
    except Exception as e:
        logger.error(f"Ошибка при автоматической активации бонусов: {str(e)}")


@actor
def bonus_statistics_update() -> None:
    """
    Задача для обновления статистики бонусов
    Запускается раз в час для сбора аналитики
    """
    try:
        total_bonuses = Bonus.objects.count()
        used_bonuses = Bonus.objects.filter(status='used').count()
        pending_bonuses = Bonus.objects.filter(status='pending').count()
        active_bonuses = Bonus.objects.filter(status='active').count()
        expired_bonuses = Bonus.objects.filter(status='expired').count()
        
        # Логируем статистику
        logger.info(f"Статистика бонусов: Всего={total_bonuses}, "
                   f"Использовано={used_bonuses}, Ожидает={pending_bonuses}, "
                   f"Активно={active_bonuses}, Истекло={expired_bonuses}")
        
        # Статистика по типам
        for bonus_type, display_name in Bonus.BONUS_TYPES:
            count = Bonus.objects.filter(bonus_type=bonus_type).count()
            used_count = Bonus.objects.filter(bonus_type=bonus_type, status='used').count()
            logger.info(f"Бонусы {display_name}: Всего={count}, Использовано={used_count}")
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении статистики бонусов: {str(e)}")


@actor
def cleanup_old_activities() -> None:
    """
    Задача для очистки старых записей активности
    Запускается раз в день для удаления записей старше 7 дней
    """
    try:
        result = ActivityService.cleanup_old_activities(days=7)
        
        if 'error' in result:
            logger.error(f"Ошибка при очистке старых записей активности: {result['error']}")
        else:
            logger.info(f"Очистка активности завершена: удалено {result['deleted_count']} записей")
            
    except Exception as e:
        logger.error(f"Критическая ошибка при очистке записей активности: {str(e)}")


@actor
def update_referral_statistics() -> None:
    """
    Задача для обновления статистики реферальной программы
    Запускается каждые 30 минут
    """
    try:
        from src.accounts.services import ReferralService
        from src.accounts.models import CustomUser, Referral
        
        # Подсчитываем общее количество рефералов
        total_referrals = Referral.objects.filter(approved=True).count()
        
        # Подсчитываем активных пользователей с рефералами
        active_referrers = CustomUser.objects.filter(
            given_referrals__approved=True
        ).distinct().count()
        
        logger.info(
            f"Статистика рефералов обновлена: {total_referrals} рефералов, "
            f"{active_referrers} активных рефереров"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении статистики рефералов: {str(e)}")


@actor
def cleanup_old_referral_bonuses() -> None:
    """
    Задача для очистки старых записей реферальных бонусов
    Запускается еженедельно для архивирования записей старше 6 месяцев
    """
    try:
        from src.accounts.models import ReferralBonus
        
        # Удаляем записи старше 6 месяцев
        cutoff_date = now() - timedelta(days=180)
        
        old_bonuses = ReferralBonus.objects.filter(
            created_at__lt=cutoff_date
        )
        
        count = old_bonuses.count()
        if count > 0:
            old_bonuses.delete()
            logger.info(f"Удалено {count} старых записей реферальных бонусов (старше 6 месяцев)")
        else:
            logger.info("Нет старых записей реферальных бонусов для удаления")
            
    except Exception as e:
        logger.error(f"Ошибка при очистке старых реферральных бонусов: {str(e)}")


@actor 
def process_pending_referrals() -> None:
    """
    Задача для обработки ожидающих одобрения рефералов
    На данный момент рефералы одобряются автоматически,
    но эта задача может быть полезна для будущих изменений
    """
    try:
        from src.accounts.models import Referral
        
        # Находим неодобренные рефералы
        pending_referrals = Referral.objects.filter(approved=False)
        count = pending_referrals.count()
        
        if count > 0:
            # Автоматически одобряем все рефералы
            pending_referrals.update(approved=True)
            logger.info(f"Автоматически одобрено {count} рефералов")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке ожидающих рефералов: {str(e)}")


@actor
def send_referral_level_notifications() -> None:
    """
    Задача для отправки уведомлений о достижении новых уровней
    Запускается каждые 2 часа
    """
    try:
        from src.accounts.models import CustomUser, ReferralLevel
        from src.accounts.services import ReferralService
        
        # Получаем всех пользователей с рефералами
        users_with_referrals = CustomUser.objects.filter(
            given_referrals__approved=True
        ).distinct()
        
        notifications_sent = 0
        
        for user in users_with_referrals:
            try:
                current_level = ReferralService.get_user_referral_level(user)
                if current_level:
                    # Здесь можно добавить логику отправки уведомлений
                    # через Telegram или другие каналы
                    pass
                    
            except Exception as e:
                logger.warning(f"Ошибка при проверке уровня для пользователя {user.username}: {str(e)}")
                continue
        
        if notifications_sent > 0:
            logger.info(f"Отправлено {notifications_sent} уведомлений о достижении уровней")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений о уровнях: {str(e)}")