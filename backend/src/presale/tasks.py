import logging
import dramatiq
from typing import Optional
from django.db import transaction
from django.utils import timezone

from .models import Presale, PresaleRound, Investment
from .services import PresaleService, PresaleRoundService

logger = logging.getLogger(__name__)


@dramatiq.actor
def check_and_advance_presale_rounds():
    """
    Проверить и перевести пресейлы к следующему раунду при достижении цели.
    Выполняется каждые 30 минут.
    """
    logger.info("Начало проверки раундов пресейла")
    
    # Получить все активные пресейлы
    active_presales = Presale.objects.filter(status='active')
    
    for presale in active_presales:
        try:
            with transaction.atomic():
                # Получить информацию о текущем раунде
                current_round_info = PresaleService.get_current_round_info(presale)
                
                # Если раунд завершен (достигнута цель), перейти к следующему
                if current_round_info['is_completed']:
                    logger.info(
                        f"Раунд {presale.current_round} пресейла {presale.id} завершен. "
                        f"Инвестировано: {current_round_info['current_investment']} / "
                        f"{current_round_info['target_investment']}"
                    )
                    
                    # Перейти к следующему раунду
                    success = PresaleService.advance_to_next_round(presale)
                    
                    if success:
                        logger.info(
                            f"Пресейл {presale.id} переведен к раунду {presale.current_round}"
                        )
                    else:
                        logger.info(
                            f"Пресейл {presale.id} завершен (все раунды пройдены)"
                        )
                        
        except Exception as e:
            logger.error(
                f"Ошибка при проверке пресейла {presale.id}: {str(e)}",
                exc_info=True
            )
    
    logger.info("Завершение проверки раундов пресейла")


@dramatiq.actor
def auto_create_presale_if_none_active():
    """
    Автоматически создать новый пресейл, если нет активных.
    Выполняется каждый час.
    """
    logger.info("Проверка наличия активного пресейла")
    
    try:
        # Проверить, есть ли активный пресейл
        active_presale = PresaleService.get_active_presale()
        
        if not active_presale:
            logger.info("Активный пресейл не найден, создаем новый")
            
            # Создать новый пресейл
            presale = PresaleService.create_presale()
            
            # Создать дефолтные раунды, если их нет
            existing_rounds_count = PresaleRound.objects.count()
            if existing_rounds_count == 0:
                logger.info("Создаем дефолтные раунды пресейла")
                PresaleRoundService.create_default_rounds()
            
            logger.info(f"Создан новый пресейл: {presale.id}")
        else:
            logger.info(f"Активный пресейл найден: {active_presale.id}")
            
    except Exception as e:
        logger.error(
            f"Ошибка при создании пресейла: {str(e)}",
            exc_info=True
        )


@dramatiq.actor  
def cleanup_old_investments(days_to_keep: int = 365):
    """
    Очистка старых инвестиций (архивирование).
    Выполняется еженедельно.
    """
    logger.info(f"Начало очистки инвестиций старше {days_to_keep} дней")
    
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        
        # Подсчитать количество старых инвестиций
        old_investments_count = Investment.objects.filter(
            created_at__lt=cutoff_date
        ).count()
        
        if old_investments_count == 0:
            logger.info("Старых инвестиций для очистки не найдено")
            return
        
        # В реальном проекте здесь можно архивировать данные
        # вместо удаления, например, перенести в отдельную таблицу
        logger.info(
            f"Найдено {old_investments_count} инвестиций для архивирования "
            f"(старше {cutoff_date})"
        )
        
        # Пока просто логируем, не удаляем
        # Investment.objects.filter(created_at__lt=cutoff_date).delete()
        
    except Exception as e:
        logger.error(
            f"Ошибка при очистке инвестиций: {str(e)}",
            exc_info=True
        )


@dramatiq.actor
def update_presale_statistics():
    """
    Обновление статистики пресейлов.
    Выполняется каждые 15 минут.
    """
    logger.info("Начало обновления статистики пресейлов")
    
    try:
        # Обновить общие суммы для всех пресейлов
        presales = Presale.objects.all()
        
        for presale in presales:
            # Пересчитать общую статистику
            investments = Investment.objects.filter(presale=presale)
            
            total_invested = sum(inv.amount for inv in investments)
            total_tokens_sold = sum(inv.tokens_received for inv in investments)
            
            # Обновить только если значения изменились
            if (presale.total_invested != total_invested or 
                presale.total_tokens_sold != total_tokens_sold):
                
                presale.total_invested = total_invested
                presale.total_tokens_sold = total_tokens_sold
                presale.save(update_fields=['total_invested', 'total_tokens_sold'])
                
                logger.info(
                    f"Обновлена статистика пресейла {presale.id}: "
                    f"{total_invested} монет, {total_tokens_sold} токенов"
                )
        
        logger.info("Завершение обновления статистики пресейлов")
        
    except Exception as e:
        logger.error(
            f"Ошибка при обновлении статистики: {str(e)}",
            exc_info=True
        )


@dramatiq.actor
def send_presale_notifications():
    """
    Отправка уведомлений о важных событиях пресейла.
    Выполняется каждые 10 минут.
    """
    logger.info("Проверка событий для уведомлений пресейла")
    
    try:
        # Проверить активные пресейлы на важные события
        active_presales = Presale.objects.filter(status='active')
        
        for presale in active_presales:
            current_round_info = PresaleService.get_current_round_info(presale)
            
            # Уведомление при достижении 90% цели раунда
            if (90 <= current_round_info['progress_percent'] < 100 and
                current_round_info['current_investment'] > 0):
                
                logger.info(
                    f"Раунд {presale.current_round} пресейла {presale.id} "
                    f"близок к завершению: {current_round_info['progress_percent']:.1f}%"
                )
                
                # Здесь можно добавить отправку уведомлений пользователям
                # например, через Telegram или email
            
            # Уведомление при завершении раунда
            if current_round_info['is_completed']:
                logger.info(
                    f"Раунд {presale.current_round} пресейла {presale.id} завершен!"
                )
        
    except Exception as e:
        logger.error(
            f"Ошибка при отправке уведомлений: {str(e)}",
            exc_info=True
        )
