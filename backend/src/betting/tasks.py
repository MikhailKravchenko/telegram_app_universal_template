import dramatiq
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from .models import GameRound, News, PlatformSettings, NewsAnalysis, NewsSource
from .services import (
    GameRoundService, NewsService, PayoutService, AnalysisService
)
from .serializers import GameRoundSerializer

logger = logging.getLogger(__name__)


@dramatiq.actor
def round_starter():
    """
    Создаёт новые короткие раунды на 5-минутную сетку времени
    """
    try:
        settings = PlatformSettings.get_current()
        
        if not settings.enabled:
            logger.info("Gaming is disabled, skipping round creation")
            return
        
        # Проверяем, нужно ли создавать новый раунд
        now = timezone.now()
        
        # Выравниваем на 5-минутную сетку
        minutes_to_next = 5 - (now.minute % 5)
        next_round_time = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_next)
        
        # Проверяем, есть ли уже короткий раунд на это время
        existing_round = GameRound.objects.filter(
            round_type='short',
            start_time=next_round_time
        ).first()
        
        if existing_round:
            logger.info(f"Short round for {next_round_time} already exists")
            return
        
        # Создаём новый короткий раунд
        round_obj = GameRoundService.create_round()
        logger.info(f"Created new short round {round_obj.id} for {round_obj.start_time}")
        
        # Отправляем WebSocket уведомление о новом раунде через Channel Layer
        _send_websocket_notification(round_obj.id, 'round_notification')
        
    except Exception as e:
        logger.error(f"Error in round_starter: {str(e)}")
        raise


@dramatiq.actor
def long_round_starter():
    """
    Создаёт длинные раунды на 24 часа
    Запускается ежедневно и создаёт раунд на следующие сутки (00:00 - 00:00)
    """
    try:
        settings = PlatformSettings.get_current()
        
        if not settings.enabled:
            logger.info("Gaming is disabled, skipping long round creation")
            return
        
        # Получаем текущее время
        now = timezone.now()
        
        # Начало следующего дня (00:00)
        next_day_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Проверяем, есть ли уже длинный раунд на следующий день
        existing_round = GameRound.objects.filter(
            round_type='long',
            start_time=next_day_start
        ).first()
        
        if existing_round:
            logger.info(f"Long round for {next_day_start} already exists")
            return
        
        # Создаём новый длинный раунд
        round_obj = GameRoundService.create_long_round()
        logger.info(f"Created new long round {round_obj.id} for {round_obj.start_time} - {round_obj.end_time}")
        
        # Отправляем WebSocket уведомление о новом длинном раунде через Channel Layer
        _send_websocket_notification(round_obj.id, 'round_notification')
        
    except Exception as e:
        logger.error(f"Error in long_round_starter: {str(e)}")
        raise


@dramatiq.actor
def round_closer_and_settler():
    """
    Закрывает раунды и обрабатывает их:
    1. Закрывает раунды, время которых истекло
    2. Назначает новости закрытым раундам
    3. Обрабатывает анализ новостей
    4. Рассчитывает и выплачивает выигрыши
    """
    try:
        _close_expired_rounds()
        _assign_news_to_closed_rounds()
        _process_pending_analysis()
        _process_payouts()
        
    except Exception as e:
        logger.error(f"Error in round_closer_and_settler: {str(e)}")
        raise


def _close_expired_rounds():
    """Закрыть раунды, время которых истекло (для коротких и длинных раундов)"""
    now = timezone.now()
    
    expired_rounds = GameRound.objects.filter(
        status='open',
        end_time__lte=now
    )
    
    for round_obj in expired_rounds:
        try:
            GameRoundService.close_round(round_obj.id)
            round_type_label = "short" if round_obj.round_type == 'short' else "long"
            logger.info(f"Closed expired {round_type_label} round {round_obj.id}")
            
            # Отправляем WebSocket уведомление о закрытии раунда через Channel Layer
            _send_websocket_notification(round_obj.id, 'round_notification')
            
        except Exception as e:
            logger.error(f"Error closing round {round_obj.id}: {str(e)}")


def _assign_news_to_closed_rounds():
    """Назначить новости закрытым раундам"""
    # Находим раунды без новостей
    rounds_without_news = GameRound.objects.filter(
        status='closed',
        news__isnull=True
    ).order_by('end_time')
    
    if not rounds_without_news.exists():
        return
    
    # Получаем доступные новости
    available_news = NewsService.get_available_news()
    
    for round_obj in rounds_without_news:
        if not available_news.exists():
            # Нет доступных новостей - отменяем раунд
            logger.warning(f"No available news for round {round_obj.id}, voiding round")
            _void_round(round_obj)
            continue
        
        # Берём самую свежую новость
        news = available_news.first()
        
        try:
            NewsService.assign_news_to_round(round_obj.id, news.id)
            logger.info(f"Assigned news {news.id} to round {round_obj.id}")
            
            # Отправляем WebSocket уведомление об обновлении раунда через Channel Layer
            _send_websocket_notification(round_obj.id, 'round_notification')
            
            # Убираем эту новость из доступных
            available_news = available_news.exclude(id=news.id)
            
        except Exception as e:
            logger.error(f"Error assigning news to round {round_obj.id}: {str(e)}")


def _process_pending_analysis():
    """Обработать ожидающие анализа новости с помощью нейросетей"""
    pending_analysis = NewsAnalysis.objects.filter(
        status='pending',
        news__status='active'
    ).select_related('news')
    
    for analysis in pending_analysis:
        try:
            # Обрабатываем анализ с помощью нейросетей
            AnalysisService.process_news_analysis(analysis.news.id)
            logger.info(f"Processed AI analysis for news {analysis.news.id}")
            
        except Exception as e:
            logger.error(f"Error processing AI analysis for news {analysis.news.id}: {str(e)}")
            
            # Помечаем анализ как неудачный
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()


def _process_payouts():
    """Обработать выплаты для завершённых раундов"""
    # Находим раунды с определённым результатом, но без выплат
    rounds_for_payout = GameRound.objects.filter(
        status='closed',
        result__isnull=False
    )
    
    for round_obj in rounds_for_payout:
        try:
            result = PayoutService.process_payouts(round_obj.id)
            logger.info(f"Processed payouts for round {round_obj.id}: {result}")
            
            # Отправляем WebSocket уведомление о завершении раунда через Channel Layer
            _send_websocket_notification(round_obj.id, 'round_notification')
            
        except Exception as e:
            logger.error(f"Error processing payouts for round {round_obj.id}: {str(e)}")


def _void_round(round_obj: GameRound):
    """Отменить раунд с возвратом ставок"""
    try:
        with transaction.atomic():
            bets = round_obj.bets.all()
            if bets.exists():
                PayoutService._process_full_refund(round_obj, bets)
                logger.info(f"Voided round {round_obj.id} with {bets.count()} refunds")
            else:
                round_obj.status = 'void'
                round_obj.resolved_at = timezone.now()
                round_obj.save()
                logger.info(f"Voided empty round {round_obj.id}")
                
    except Exception as e:
        logger.error(f"Error voiding round {round_obj.id}: {str(e)}")


@dramatiq.actor
def news_fetcher():
    """
    Загружает новые новости из RSS источников
    """
    try:
        logger.info("News fetcher started - fetching fresh news from RSS sources")
        
        # Получаем самую свежую новость (не старше 5 минут)
        fresh_news = NewsService.fetch_fresh_news()
        
        if fresh_news:
            logger.info(f"Successfully fetched fresh news: {fresh_news.title[:50]}...")
        else:
            logger.warning("No fresh news found from RSS sources")
            # Создаём тестовые новости только если нет активных источников
            _create_mock_news_if_no_sources()
        
    except Exception as e:
        logger.error(f"Error in news_fetcher: {str(e)}")
        raise


def _create_mock_news_if_no_sources():
    """Создать тестовые новости если нет активных RSS источников"""
    # Проверяем, есть ли активные источники
    active_sources = NewsSource.objects.filter(enabled=True, status='active').exists()
    
    if active_sources:
        logger.info("Active RSS sources found, skipping mock news creation")
        return
    
    # Проверяем количество доступных новостей
    pending_news_count = News.objects.filter(status='pending').count()
    
    if pending_news_count < 3:  # Поддерживаем минимум 3 новости
        logger.info("No active RSS sources and insufficient news, creating mock news")
        
        mock_news_data = [
            {
                'title': 'Tech Giant Reports Strong Q4 Earnings Growth',
                'content': 'Major technology company exceeded expectations with 15% revenue growth in the fourth quarter, driven by strong demand for cloud services and AI products. The company reported record-breaking profits and optimistic outlook for the coming year.',
                'category': 'technology',
                'source_url': f'https://example.com/tech-earnings-{timezone.now().timestamp()}'
            },
            {
                'title': 'Market Volatility Continues Amid Economic Uncertainty',
                'content': 'Stock markets showed mixed signals as investors react to recent policy changes and economic indicators. Trading volumes remain high as market participants navigate through uncertain economic conditions and geopolitical tensions.',
                'category': 'finance',
                'source_url': f'https://example.com/market-volatility-{timezone.now().timestamp()}'
            },
            {
                'title': 'Breakthrough in Renewable Energy Technology Announced',
                'content': 'Scientists unveil new solar panel technology promising 40% efficiency gains over current models. The breakthrough could significantly reduce the cost of renewable energy and accelerate the transition to clean power sources worldwide.',
                'category': 'technology',
                'source_url': f'https://example.com/renewable-breakthrough-{timezone.now().timestamp()}'
            }
        ]
        
        for i, news_data in enumerate(mock_news_data):
            if pending_news_count + i >= 3:
                break
                
            try:
                NewsService.create_news(**news_data)
                logger.info(f"Created mock news: {news_data['title']}")
            except Exception as e:
                logger.error(f"Error creating mock news: {str(e)}")
    else:
        logger.info(f"Sufficient news available ({pending_news_count} pending), skipping mock news creation")


@dramatiq.actor
def orphan_guard():
    """
    Проверяет и исправляет зависшие процессы:
    - Раунды, которые слишком долго в статусе 'closed'
    - Анализы, которые зависли в 'pending'
    - Очистка старых данных
    """
    try:
        _fix_stuck_rounds()
        _fix_stuck_analysis()
        _cleanup_old_data()
        
    except Exception as e:
        logger.error(f"Error in orphan_guard: {str(e)}")
        raise


def _fix_stuck_rounds():
    """Исправить зависшие раунды"""
    # Раунды, которые закрыты больше 10 минут но не обработаны
    cutoff_time = timezone.now() - timedelta(minutes=10)
    
    stuck_rounds = GameRound.objects.filter(
        status='closed',
        end_time__lt=cutoff_time,
        resolved_at__isnull=True
    )
    
    for round_obj in stuck_rounds:
        logger.warning(f"Found stuck round {round_obj.id}, attempting to fix")
        
        if round_obj.news and round_obj.result:
            # Есть новость и результат - обрабатываем выплаты
            try:
                PayoutService.process_payouts(round_obj.id)
                logger.info(f"Fixed stuck round {round_obj.id} with payouts")
            except Exception as e:
                logger.error(f"Failed to fix round {round_obj.id}: {str(e)}")
        else:
            # Нет новости или результата - отменяем
            _void_round(round_obj)


def _fix_stuck_analysis():
    """Исправить зависшие анализы"""
    # Анализы, которые больше 5 минут в pending
    cutoff_time = timezone.now() - timedelta(minutes=5)
    
    stuck_analysis = NewsAnalysis.objects.filter(
        status='pending',
        created_at__lt=cutoff_time
    )
    
    for analysis in stuck_analysis:
        try:
            # Принудительно обрабатываем с помощью нейросетей
            AnalysisService.process_news_analysis(analysis.news.id)
            logger.info(f"Fixed stuck analysis for news {analysis.news.id}")
        except Exception as e:
            logger.error(f"Failed to fix analysis {analysis.id}: {str(e)}")
            
            # Помечаем как неудачный
            analysis.status = 'failed'
            analysis.error_message = f"Stuck analysis fix failed: {str(e)}"
            analysis.save()


def _cleanup_old_data():
    """Очистка старых данных"""
    # Удаляем старые pending новости (старше 2 часов)
    old_news_cutoff = timezone.now() - timedelta(hours=2)
    
    old_pending_news = News.objects.filter(
        status='pending',
        created_at__lt=old_news_cutoff
    )
    
    deleted_count = old_pending_news.count()
    if deleted_count > 0:
        old_pending_news.delete()
        logger.info(f"Cleaned up {deleted_count} old pending news")





# Задачи для ручного запуска из админки или API
@dramatiq.actor
def manual_create_round():
    """Ручное создание короткого раунда"""
    return round_starter()


@dramatiq.actor
def manual_create_long_round():
    """Ручное создание длинного раунда"""
    return long_round_starter()


@dramatiq.actor  
def manual_process_round(round_id: int):
    """Ручная обработка конкретного раунда"""
    try:
        round_obj = GameRound.objects.get(id=round_id)
        
        if round_obj.status == 'open' and round_obj.end_time <= timezone.now():
            GameRoundService.close_round(round_id)
        
        if round_obj.status == 'closed' and not round_obj.news:
            available_news = NewsService.get_available_news()
            if available_news.exists():
                NewsService.assign_news_to_round(round_id, available_news.first().id)
        
        if round_obj.news and not round_obj.result:
            AnalysisService.process_news_analysis(round_obj.news.id)
        
        if round_obj.result and round_obj.status != 'finished':
            PayoutService.process_payouts(round_id)
            
        logger.info(f"Manually processed round {round_id}")
        
    except Exception as e:
        logger.error(f"Error manually processing round {round_id}: {str(e)}")
        raise


def _send_websocket_notification(round_id: int, notification_type: str):
    """
    Отправить WebSocket уведомление о раунде через Redis Channel Layer
    
    Args:
        round_id: ID раунда
        notification_type: Тип уведомления ('round_created', 'round_updated', 'round_closed', 'round_finished')
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        # Получаем объект раунда
        round_obj = GameRound.objects.get(id=round_id)
        
        # Сериализуем данные раунда
        serializer = GameRoundSerializer(round_obj)
        round_data = serializer.data
        
        # Получаем channel layer
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("Channel layer not available for WebSocket notifications")
            return
        
        # Отправляем уведомление в группу
        async_to_sync(channel_layer.group_send)(
            'round_notifications',
            {
                'type': 'round_notification',
                'notification_type': notification_type,
                'round_data': round_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Отправляем обновление статистики для конкретного раунда
        _send_round_stats_update(round_id)
        
        logger.info(f"Sent WebSocket notification: {notification_type} for round {round_id}")
        
    except GameRound.DoesNotExist:
        logger.error(f"Round {round_id} not found for WebSocket notification")
    except Exception as e:
        logger.error(f"Error sending WebSocket notification: {str(e)}")


def _send_round_stats_update(round_id: int):
    """
    Отправить обновление статистики раунда через WebSocket
    
    Args:
        round_id: ID раунда
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        # Получаем объект раунда
        round_obj = GameRound.objects.get(id=round_id)
        
        # Получаем статистику раунда
        bets = round_obj.bets.all()
        total_bets = bets.count()
        positive_bets = bets.filter(choice='positive').count()
        negative_bets = bets.filter(choice='negative').count()
        
        total_amount = sum(bet.amount for bet in bets)
        positive_amount = sum(bet.amount for bet in bets if bet.choice == 'positive')
        negative_amount = sum(bet.amount for bet in bets if bet.choice == 'negative')
        
        # Расчёт коэффициентов
        settings = PlatformSettings.get_current()
        fee_rate = settings.platform_fee_rate
        
        positive_coefficient = None
        negative_coefficient = None
        
        if total_amount > 0:
            available_for_payout = total_amount * (1 - fee_rate)
            
            if positive_amount > 0:
                positive_coefficient = round(available_for_payout / positive_amount, 4)
            if negative_amount > 0:
                negative_coefficient = round(available_for_payout / negative_amount, 4)
        
        stats_data = {
            'round_id': round_id,
            'status': round_obj.status,
            'total_bets': total_bets,
            'positive_bets': positive_bets,
            'negative_bets': negative_bets,
            'total_amount': total_amount,
            'positive_amount': positive_amount,
            'negative_amount': negative_amount,
            'positive_coefficient': positive_coefficient,
            'negative_coefficient': negative_coefficient,
            'time_remaining': max(0, (round_obj.end_time - timezone.now()).total_seconds()) if round_obj.status == 'open' else 0
        }
        
        # Получаем channel layer
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Отправляем обновление статистики
        async_to_sync(channel_layer.group_send)(
            f'round_stats_{round_id}',
            {
                'type': 'round_stats_update',
                'round_id': round_id,
                'stats_data': stats_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.info(f"Sent round stats update for round {round_id}")
        
    except GameRound.DoesNotExist:
        logger.error(f"Round {round_id} not found for stats update")
    except Exception as e:
        logger.error(f"Error sending round stats update: {str(e)}")



