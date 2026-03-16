import logging
import feedparser
import requests
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import (
    PlatformSettings, GameRound, Bet, News, NewsAnalysis, RoundStats, NewsSource
)
from src.accounts.models import CustomUser, UserBalance, Transaction, Bonus, BonusSettings
from src.accounts.services import BonusService, ActivityService
logger = logging.getLogger(__name__)

User = get_user_model()


class BettingService:
    """
    Сервис для управления ставками
    """
    
    @staticmethod
    def place_bet(user: CustomUser, round_id: int, amount: int, choice: str) -> Bet:
        """
        Сделать ставку
        """
        with transaction.atomic():
            # Получаем раунд и проверяем его статус
            try:
                game_round = GameRound.objects.select_for_update().get(id=round_id)
            except GameRound.DoesNotExist:
                raise ValidationError("Game round not found")
            
            if game_round.status != 'open':
                raise ValidationError("Betting is closed for this round")
            
            if game_round.end_time <= timezone.now():
                raise ValidationError("Round has already ended")
            
            # Проверяем лимиты ставки
            settings = PlatformSettings.get_current()
            if amount < settings.min_bet:
                raise ValidationError(f"Minimum bet is {settings.min_bet}")
            if amount > settings.max_bet:
                raise ValidationError(f"Maximum bet is {settings.max_bet}")
            
            # Проверяем баланс пользователя
            try:
                user_balance = user.balance
                if user_balance.coins_balance < amount:
                    raise ValidationError("Insufficient balance")
            except UserBalance.DoesNotExist:
                raise ValidationError("User balance not found")
            
            # Проверяем, что пользователь ещё не делал ставку в этом раунде
            if Bet.objects.filter(user=user, round=game_round).exists():
                raise ValidationError("You have already placed a bet in this round")
            
            # Создаём ставку
            bet = Bet.objects.create(
                user=user,
                round=game_round,
                amount=amount,
                choice=choice,
                status='pending'
            )
            
            # Списываем средства
            Transaction.objects.create(
                user=user,
                amount=-amount,
                type='bet',
                description=f"Bet placed on {choice} in round {round_id}",
                reference_id=str(bet.id)
            )
            
            # Обновляем агрегаты раунда
            game_round.update_pot_totals()
            
            # Проверяем бонус за первую ставку
            try:
                created, message, bonus = BonusService.check_first_bet_bonus(user, str(bet.id))
                if created and bonus:
                    logger.info(f"Начислен бонус за первую ставку пользователю {user.username}: {message}")
            except Exception as e:
                # Не прерываем процесс создания ставки из-за ошибки с бонусом
                logger.error(f"Ошибка при проверке бонуса за первую ставку для {user.username}: {str(e)}")
            
            # Регистрируем активность для системы активных ставок
            try:
                success, activity_message = ActivityService.record_bet_activity(user)
                if success:
                    logger.debug(f"Зарегистрирована активность ставки для {user.username}: {activity_message}")
            except Exception as e:
                # Не прерываем процесс создания ставки из-за ошибки с активностью
                logger.error(f"Ошибка при регистрации активности ставки для {user.username}: {str(e)}")
            
            return bet
    
    @staticmethod
    def get_user_bets(user: CustomUser, limit: int = 50) -> List[Bet]:
        """
        Получить ставки пользователя
        """
        return Bet.objects.filter(user=user).select_related('round', 'round__news').order_by('-created_at')[:limit]
    
    @staticmethod
    def get_round_bets(round_id: int) -> Dict[str, Any]:
        """
        Получить статистику ставок по раунду
        """
        try:
            game_round = GameRound.objects.get(id=round_id)
        except GameRound.DoesNotExist:
            raise ValidationError("Game round not found")
        
        bets = game_round.bets.all()
        
        return {
            'round_id': round_id,
            'total_bets': bets.count(),
            'total_amount': sum(bet.amount for bet in bets),
            'positive_bets': bets.filter(choice='positive').count(),
            'negative_bets': bets.filter(choice='negative').count(),
            'positive_amount': sum(bet.amount for bet in bets if bet.choice == 'positive'),
            'negative_amount': sum(bet.amount for bet in bets if bet.choice == 'negative'),
        }


class GameRoundService:
    """
    Сервис для управления игровыми раундами
    """
    
    @staticmethod
    def create_round() -> GameRound:
        """
        Создать новый короткий раунд (5 минут)
        """
        settings = PlatformSettings.get_current()
        
        if not settings.enabled:
            raise ValidationError("Gaming is disabled")
        
        # Выравниваем время на 5-минутную сетку
        now = timezone.now()
        minutes_to_add = 5 - (now.minute % 5)
        start_time = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
        end_time = start_time + timedelta(seconds=settings.round_duration_seconds)
        
        # Проверяем, что нет пересекающихся КОРОТКИХ раундов
        overlapping = GameRound.objects.filter(
            round_type='short',  # Проверяем только короткие раунды
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=['open', 'closed']
        ).exists()
        
        if overlapping:
            raise ValidationError("Overlapping short round exists")
        
        round_obj = GameRound.objects.create(
            round_type='short',
            start_time=start_time,
            end_time=end_time,
            status='open'
        )
        
        # Создаём статистику для раунда
        RoundStats.objects.create(round=round_obj)
        
        return round_obj
    
    @staticmethod
    def create_long_round() -> GameRound:
        """
        Создать новый длинный раунд (24 часа)
        Создается на следующие сутки с 00:00 до 00:00
        """
        settings = PlatformSettings.get_current()
        
        if not settings.enabled:
            raise ValidationError("Gaming is disabled")
        
        # Получаем текущее время
        now = timezone.now()
        
        # Начало следующего дня (00:00)
        next_day_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = next_day_start + timedelta(days=1)
        
        # Проверяем, что нет пересекающихся ДЛИННЫХ раундов
        overlapping = GameRound.objects.filter(
            round_type='long',  # Проверяем только длинные раунды
            start_time__lt=end_time,
            end_time__gt=next_day_start,
            status__in=['open', 'closed']
        ).exists()
        
        if overlapping:
            raise ValidationError("Overlapping long round exists")
        
        round_obj = GameRound.objects.create(
            round_type='long',
            start_time=next_day_start,
            end_time=end_time,
            status='open'
        )
        
        # Создаём статистику для раунда
        RoundStats.objects.create(round=round_obj)
        
        return round_obj
    
    @staticmethod
    def close_round(round_id: int) -> GameRound:
        """
        Закрыть раунд для приёма ставок
        """
        with transaction.atomic():
            try:
                game_round = GameRound.objects.select_for_update().get(id=round_id)
            except GameRound.DoesNotExist:
                raise ValidationError("Game round not found")
            
            if game_round.status != 'open':
                raise ValidationError("Round is not open")
            
            game_round.status = 'closed'
            game_round.save()
            
            return game_round
    
    @staticmethod
    def get_current_round() -> Optional[GameRound]:
        """
        Получить текущий активный раунд (первый найденный)
        """
        return GameRound.objects.filter(
            status='open',
            start_time__lte=timezone.now(),
            end_time__gt=timezone.now()
        ).first()
    
    @staticmethod
    def get_current_rounds():
        """
        Получить все текущие активные раунды (и short, и long)
        """
        return GameRound.objects.filter(
            status='open',
            start_time__lte=timezone.now(),
            end_time__gt=timezone.now()
        ).order_by('round_type', 'start_time')
    
    @staticmethod
    def get_recent_rounds(limit: int = 10) -> List[GameRound]:
        """
        Получить последние раунды
        """
        return GameRound.objects.select_related('news').order_by('-start_time')[:limit]


class BaseFeedParser(ABC):
    """
    Абстрактный базовый класс для парсеров фидов
    """
    
    @abstractmethod
    def parse_feed(self, source: NewsSource) -> List[Dict[str, Any]]:
        """
        Парсить фид источника
        
        Args:
            source: Объект источника новостей
            
        Returns:
            List[Dict]: Список новостей из фида
        """
        pass
    
    @staticmethod
    def _clean_html(html_content: str) -> str:
        """
        Очистить HTML теги из контента
        """
        import re
        
        # Удаляем HTML теги
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', html_content)
        
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def _passes_filters(title: str, content: str, source: NewsSource) -> bool:
        """
        Проверить, проходит ли новость через фильтры источника
        """
        text_to_check = f"{title} {content}".lower()
        
        # Проверяем ключевые слова для исключения
        exclude_keywords = source.get_exclude_keywords_list()
        for keyword in exclude_keywords:
            if keyword.lower() in text_to_check:
                return False
        
        # Проверяем ключевые слова для фильтрации
        include_keywords = source.get_keywords_list()
        if include_keywords:
            for keyword in include_keywords:
                if keyword.lower() in text_to_check:
                    return True
            return False  # Если есть фильтры, но ни один не подошёл
        
        return True  # Если нет фильтров, пропускаем
    
    @staticmethod
    def _extract_image_url(entry) -> str:
        """
        Извлечь URL изображения из записи фида
        """
        image_url = ''
        
        # Проверяем media_content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if media.get('type', '').startswith('image/'):
                    image_url = media.get('url', '')
                    break
        
        # Проверяем enclosures
        elif hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href', '')
                    break
        
        # Проверяем media_thumbnail
        elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            if isinstance(entry.media_thumbnail, list) and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get('url', '')
            elif hasattr(entry.media_thumbnail, 'url'):
                image_url = entry.media_thumbnail.url
        
        return image_url
    
    @staticmethod
    def _extract_published_time(entry) -> Optional[datetime]:
        """
        Извлечь время публикации из записи фида
        """
        published_time = None
        
        # Проверяем published_parsed
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_time = datetime(*entry.published_parsed[:6])
            published_time = timezone.make_aware(published_time)
        
        # Проверяем updated_parsed
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published_time = datetime(*entry.updated_parsed[:6])
            published_time = timezone.make_aware(published_time)
        
        return published_time


class FeedParserService(BaseFeedParser):
    """
    Универсальный сервис для парсинга различных типов фидов
    """
    
    @staticmethod
    def parse_feed(source: NewsSource) -> List[Dict[str, Any]]:
        """
        Парсить фид источника в зависимости от его типа
        
        Args:
            source: Объект источника новостей
            
        Returns:
            List[Dict]: Список новостей из фида
        """
        try:
            # Получаем фид
            response = requests.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Выбираем парсер в зависимости от типа источника
            if source.source_type in ['rss', 'atom', 'feed']:
                return FeedParserService._parse_with_feedparser(source, response.content)
            elif source.source_type == 'json':
                return FeedParserService._parse_json_feed(source, response.content)
            else:
                logger.error(f"Unsupported source type: {source.source_type}")
                source.update_parsing_stats(success=False, error_message=f"Unsupported source type: {source.source_type}")
                return []
                
        except requests.RequestException as e:
            error_msg = f"Failed to fetch feed: {str(e)}"
            logger.error(f"Feed fetch error for {source.name}: {error_msg}")
            source.update_parsing_stats(success=False, error_message=error_msg)
            return []
        except Exception as e:
            error_msg = f"Feed parsing error: {str(e)}"
            logger.error(f"Feed parsing error for {source.name}: {error_msg}")
            source.update_parsing_stats(success=False, error_message=error_msg)
            return []
    
    @staticmethod
    def _parse_with_feedparser(source: NewsSource, content: bytes) -> List[Dict[str, Any]]:
        """
        Парсить фид с помощью feedparser (RSS, Atom, Generic)
        """
        # Парсим фид
        feed = feedparser.parse(content)
        
        if feed.bozo:
            logger.warning(f"Feed parsing warning for {source.name}: {feed.bozo_exception}")
        
        news_items = []
        
        for entry in feed.entries[:source.max_items_per_update]:
            try:
                # Извлекаем данные новости
                title = getattr(entry, 'title', '').strip()
                if not title:
                    continue
                
                # Получаем контент
                content = ''
                if hasattr(entry, 'summary'):
                    content = entry.summary
                elif hasattr(entry, 'description'):
                    content = entry.description
                elif hasattr(entry, 'content') and entry.content:
                    content = entry.content[0].value if isinstance(entry.content, list) else str(entry.content)
                
                # Очищаем HTML теги
                content = FeedParserService._clean_html(content)
                
                # Проверяем минимальную длину контента
                if len(content) < source.min_content_length:
                    continue
                
                # Получаем URL новости
                link = getattr(entry, 'link', '')
                if not link:
                    continue
                
                # Получаем изображение
                image_url = FeedParserService._extract_image_url(entry)
                
                # Получаем дату публикации
                published_time = FeedParserService._extract_published_time(entry)
                
                # Применяем фильтры
                if not FeedParserService._passes_filters(title, content, source):
                    continue
                
                news_item = {
                    'title': title,
                    'content': content,
                    'source_url': link,
                    'image_url': image_url,
                    'category': source.category,
                    'language': source.language,
                    'published_time': published_time,
                    'source': source
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                logger.error(f"Error parsing feed entry from {source.name}: {str(e)}")
                continue
        
        # Обновляем статистику источника
        source.update_parsing_stats(success=True)
        
        return news_items
    
    @staticmethod
    def _parse_json_feed(source: NewsSource, content: bytes) -> List[Dict[str, Any]]:
        """
        Парсить JSON Feed (JSON Feed 1.1 specification)
        """
        try:
            feed_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {source.name}: {str(e)}")
            source.update_parsing_stats(success=False, error_message=f"JSON decode error: {str(e)}")
            return []
        
        news_items = []
        items = feed_data.get('items', [])
        
        for item in items[:source.max_items_per_update]:
            try:
                # Извлекаем данные новости
                title = item.get('title', '').strip()
                if not title:
                    continue
                
                # Получаем контент
                content = item.get('content_text', '') or item.get('content_html', '')
                if content:
                    content = FeedParserService._clean_html(content)
                
                # Проверяем минимальную длину контента
                if len(content) < source.min_content_length:
                    continue
                
                # Получаем URL новости
                link = item.get('url', '')
                if not link:
                    continue
                
                # Получаем изображение
                image_url = ''
                if 'image' in item:
                    image_url = item['image']
                elif 'attachments' in item:
                    for attachment in item['attachments']:
                        if attachment.get('mime_type', '').startswith('image/'):
                            image_url = attachment.get('url', '')
                            break
                
                # Получаем дату публикации
                published_time = None
                if 'date_published' in item:
                    try:
                        published_time = datetime.fromisoformat(item['date_published'].replace('Z', '+00:00'))
                        if published_time.tzinfo is None:
                            published_time = timezone.make_aware(published_time)
                    except ValueError:
                        pass
                
                # Применяем фильтры
                if not FeedParserService._passes_filters(title, content, source):
                    continue
                
                news_item = {
                    'title': title,
                    'content': content,
                    'source_url': link,
                    'image_url': image_url,
                    'category': source.category,
                    'language': source.language,
                    'published_time': published_time,
                    'source': source
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                logger.error(f"Error parsing JSON feed item from {source.name}: {str(e)}")
                continue
        
        # Обновляем статистику источника
        source.update_parsing_stats(success=True)
        
        return news_items


class RSSParserService(BaseFeedParser):
    """
    Сервис для парсинга RSS лент (для обратной совместимости)
    """
    
    @staticmethod
    def parse_rss_feed(source: NewsSource) -> List[Dict[str, Any]]:
        """
        Парсить RSS ленту источника (обёртка для обратной совместимости)
        """
        return FeedParserService.parse_feed(source)


class NewsService:
    """
    Сервис для управления новостями
    """
    
    @staticmethod
    def create_news(title: str, content: str, source_url: str, 
                   category: str = 'general', image_url: str = None, 
                   language: str = 'en', source: NewsSource = None) -> News:
        """
        Создать новость
        """
        # Проверяем дубликаты по source_url
        if News.objects.filter(source_url=source_url).exists():
            raise ValidationError("News with this source URL already exists")
        
        news = News.objects.create(
            title=title,
            content=content,
            source_url=source_url,
            source=source,
            category=category,
            image_url=image_url,
            language=language,
            status='pending'
        )
        
        # Создаём запись для анализа
        NewsAnalysis.objects.create(news=news, status='pending')
        
        return news
    
    @staticmethod
    def get_available_news() -> List[News]:
        """
        Получить доступные для назначения новости
        """
        settings = PlatformSettings.get_current()
        cutoff_time = timezone.now() - timedelta(minutes=settings.news_freshness_minutes)
        
        return News.objects.filter(
            status='pending',
            created_at__gte=cutoff_time
        ).order_by('-created_at')
    
    @staticmethod
    def assign_news_to_round(round_id: int, news_id: int) -> GameRound:
        """
        Назначить новость раунду
        """
        with transaction.atomic():
            try:
                game_round = GameRound.objects.select_for_update().get(id=round_id)
                news = News.objects.select_for_update().get(id=news_id)
            except GameRound.DoesNotExist:
                raise ValidationError("Game round not found")
            except News.DoesNotExist:
                raise ValidationError("News not found")
            
            if game_round.status != 'closed':
                raise ValidationError("Round must be closed to assign news")
            
            if news.status != 'pending':
                raise ValidationError("News is not available for assignment")
            
            # Назначаем новость
            game_round.news = news
            game_round.save()
            
            # Помечаем новость как активную
            news.status = 'active'
            news.save()
            
            return game_round
    
    @staticmethod
    def fetch_fresh_news() -> Optional[News]:
        """
        Получить самую свежую новость (не старше 5 минут)
        Если не найдена, вернуть самую свежую доступную
        """
        now = timezone.now()
        five_minutes_ago = now - timedelta(minutes=5)
        
        # Получаем активные источники, отсортированные по приоритету
        active_sources = NewsSource.objects.filter(
            enabled=True,
            status='active'
        ).order_by('priority', 'name')
        
        if not active_sources.exists():
            logger.warning("No active news sources found")
            return None
        
        # Ищем новость не старше 5 минут
        for source in active_sources:
            try:
                # Парсим фид источника
                news_items = FeedParserService.parse_feed(source)
                
                if not news_items:
                    continue
                
                # Ищем самую свежую новость
                for news_item in news_items:
                    # Проверяем возраст новости
                    published_time = news_item.get('published_time')
                    if published_time and published_time >= five_minutes_ago:
                        # Создаём новость
                        news = NewsService._create_news_from_item(news_item)
                        if news:
                            logger.info(f"Found fresh news from {source.name}: {news.title[:50]}...")
                            return news
                
                # Если не нашли свежую, берём самую свежую из этого источника
                if news_items:
                    news_item = news_items[0]  # Первая в списке - самая свежая
                    news = NewsService._create_news_from_item(news_item)
                    if news:
                        logger.info(f"Found recent news from {source.name}: {news.title[:50]}...")
                        return news
                        
            except Exception as e:
                logger.error(f"Error processing source {source.name}: {str(e)}")
                continue
        
        # Если ничего не нашли, возвращаем самую свежую доступную новость
        available_news = NewsService.get_available_news()
        if available_news.exists():
            return available_news.first()
        
        return None
    
    @staticmethod
    def _create_news_from_item(news_item: Dict[str, Any]) -> Optional[News]:
        """
        Создать новость из элемента фида
        """
        try:
            # Проверяем дубликаты по source_url
            if News.objects.filter(source_url=news_item['source_url']).exists():
                return None
            
            # Создаём новость
            news = News.objects.create(
                title=news_item['title'],
                content=news_item['content'],
                source_url=news_item['source_url'],
                source=news_item.get('source'),  # Передаём источник
                category=news_item['category'],
                image_url=news_item.get('image_url', ''),
                language=news_item['language'],
                status='pending'
            )
            
            # Создаём запись для анализа
            NewsAnalysis.objects.create(news=news, status='pending')
            
            return news
            
        except Exception as e:
            logger.error(f"Error creating news from feed item: {str(e)}")
            return None


class PayoutService:
    """
    Сервис для расчёта и выплаты выигрышей
    """
    
    @staticmethod
    def calculate_payouts(round_id: int) -> Dict[str, Any]:
        """
        Рассчитать выплаты для раунда
        """
        try:
            game_round = GameRound.objects.get(id=round_id)
        except GameRound.DoesNotExist:
            raise ValidationError("Game round not found")
        
        if game_round.result is None:
            raise ValidationError("Round result not determined")
        
        bets = game_round.bets.all()
        if not bets.exists():
            return {'message': 'No bets to process'}
        
        settings = PlatformSettings.get_current()
        fee_rate = settings.platform_fee_rate
        
        # Общий банк
        total_pot = sum(bet.amount for bet in bets)
        
        # Комиссия платформы
        platform_fee = int(total_pot * fee_rate)
        available_for_payout = total_pot - platform_fee
        
        # Ставки победителей
        winning_bets = bets.filter(choice=game_round.result)
        if not winning_bets.exists():
            # Если никто не угадал - возврат всем
            return PayoutService._process_full_refund(game_round, bets)
        
        # Сумма ставок победителей
        winning_amount = sum(bet.amount for bet in winning_bets)
        
        # Коэффициент выплаты
        payout_coefficient = Decimal(available_for_payout) / Decimal(winning_amount)
        
        payouts = []
        for bet in winning_bets:
            payout_amount = int(bet.amount * payout_coefficient)
            payouts.append({
                'bet_id': bet.id,
                'user_id': bet.user.id,
                'bet_amount': bet.amount,
                'payout_amount': payout_amount,
                'coefficient': payout_coefficient
            })
        
        return {
            'total_pot': total_pot,
            'platform_fee': platform_fee,
            'available_for_payout': available_for_payout,
            'winning_bets_count': winning_bets.count(),
            'winning_amount': winning_amount,
            'payout_coefficient': payout_coefficient,
            'payouts': payouts
        }
    
    @staticmethod
    def process_payouts(round_id: int) -> Dict[str, Any]:
        """
        Обработать выплаты для раунда
        """
        with transaction.atomic():
            try:
                game_round = GameRound.objects.select_for_update().get(id=round_id)
            except GameRound.DoesNotExist:
                raise ValidationError("Game round not found")
            
            if game_round.status == 'finished':
                raise ValidationError("Payouts already processed")
            
            if game_round.status != 'closed':
                raise ValidationError("Round must be closed")
            
            if game_round.result is None:
                raise ValidationError("Round result not determined")
            
            bets = game_round.bets.select_for_update().all()
            if not bets.exists():
                game_round.status = 'finished'
                game_round.resolved_at = timezone.now()
                game_round.save()
                return {'message': 'No bets to process'}
            
            settings = PlatformSettings.get_current()
            fee_rate = settings.platform_fee_rate
            
            # Проверяем, есть ли ставки только на одну сторону
            positive_bets = bets.filter(choice='positive')
            negative_bets = bets.filter(choice='negative')
            
            if not positive_bets.exists() or not negative_bets.exists():
                # Возврат всем
                return PayoutService._process_full_refund(game_round, bets)
            
            # Обычная обработка выплат
            total_pot = sum(bet.amount for bet in bets)
            platform_fee = int(total_pot * fee_rate)
            available_for_payout = total_pot - platform_fee
            
            winning_bets = bets.filter(choice=game_round.result)
            losing_bets = bets.exclude(choice=game_round.result)
            
            if not winning_bets.exists():
                return PayoutService._process_full_refund(game_round, bets)
            
            winning_amount = sum(bet.amount for bet in winning_bets)
            payout_coefficient = Decimal(available_for_payout) / Decimal(winning_amount)
            
            # Обрабатываем выплаты победителям
            total_paid = 0
            for bet in winning_bets:
                payout_amount = int(bet.amount * payout_coefficient)
                
                # Создаём транзакцию выплаты
                Transaction.objects.create(
                    user=bet.user,
                    amount=payout_amount,
                    type='win',
                    description=f"Win payout for round {round_id}",
                    reference_id=str(bet.id)
                )
                
                # Обновляем ставку
                bet.status = 'won'
                bet.payout_amount = payout_amount
                bet.payout_coefficient = payout_coefficient
                bet.save()
                
                total_paid += payout_amount
            
            # Помечаем проигравшие ставки
            for bet in losing_bets:
                bet.status = 'lost'
                bet.save()
            
            # Создаём транзакцию комиссии платформы (на системного пользователя)
            system_user, created = CustomUser.objects.get_or_create(
                username='system',
                defaults={'email': 'system@platform.com'}
            )
            
            Transaction.objects.create(
                user=system_user,
                amount=platform_fee,
                type='platform_fee',
                description=f"Platform fee from round {round_id}",
                reference_id=str(round_id)
            )
            
            # Обновляем раунд
            game_round.status = 'finished'
            game_round.resolved_at = timezone.now()
            game_round.fee_applied_rate = fee_rate
            game_round.save()
            
            # Обновляем статистику
            PayoutService._update_round_stats(game_round, total_paid, platform_fee)
            
            return {
                'total_pot': total_pot,
                'platform_fee': platform_fee,
                'total_paid': total_paid,
                'winning_bets': winning_bets.count(),
                'losing_bets': losing_bets.count(),
                'payout_coefficient': payout_coefficient
            }
    
    @staticmethod
    def _process_full_refund(game_round: GameRound, bets) -> Dict[str, Any]:
        """
        Обработать полный возврат всех ставок
        """
        total_refunded = 0
        
        for bet in bets:
            # Создаём транзакцию возврата
            Transaction.objects.create(
                user=bet.user,
                amount=bet.amount,
                type='refund',
                description=f"Refund for round {game_round.id}",
                reference_id=str(bet.id)
            )
            
            bet.status = 'refunded'
            bet.payout_amount = bet.amount
            bet.save()
            
            total_refunded += bet.amount
        
        game_round.status = 'void'
        game_round.resolved_at = timezone.now()
        game_round.save()
        
        return {
            'message': 'Full refund processed',
            'total_refunded': total_refunded,
            'refunded_bets': bets.count()
        }
    
    @staticmethod
    def _update_round_stats(game_round: GameRound, total_payout: int, platform_fee: int):
        """
        Обновить статистику раунда
        """
        try:
            stats = game_round.stats
        except RoundStats.DoesNotExist:
            stats = RoundStats.objects.create(round=game_round)
        
        stats.calculate_stats()
        stats.total_payout = total_payout
        stats.platform_fee = platform_fee
        stats.save()


class AnalysisService:
    """
    Сервис для анализа новостей с использованием нейросетей
    """
    
    @staticmethod
    def process_news_analysis(news_id: int, mock_result: str = None) -> NewsAnalysis:
        """
        Обработать анализ новости с помощью нейросетей
        
        Args:
            news_id: ID новости для анализа
            mock_result: Принудительный результат для тестирования
            
        Returns:
            NewsAnalysis: Результат анализа
        """
        try:
            news = News.objects.get(id=news_id)
            analysis = news.analysis
        except News.DoesNotExist:
            raise ValidationError("News not found")
        except NewsAnalysis.DoesNotExist:
            raise ValidationError("News analysis not found")
        
        if analysis.status != 'pending':
            raise ValidationError("Analysis already processed")
        
        # Если передан mock_result, используем его для тестирования
        if mock_result:
            return AnalysisService._process_mock_analysis(analysis, news, mock_result)
        
        # Используем реальный анализ с OpenAI
        try:
            from .openai_sentiment_service import OpenAISentimentService
            
            # Выполняем анализ тональности
            sentiment_result = OpenAISentimentService.analyze_sentiment(
                title=news.title,
                content=news.content,
                url=news.source_url
            )
            
            # Обновляем анализ с результатами
            analysis.status = 'processed'
            analysis.label = sentiment_result.label.value
            analysis.score = Decimal(str(sentiment_result.confidence))
            analysis.provider = sentiment_result.provider
            analysis.model_name = sentiment_result.model
            analysis.confidence_score = Decimal(str(sentiment_result.confidence))
            analysis.processing_time = sentiment_result.processing_time
            analysis.raw_response = sentiment_result.raw_response
            analysis.error_message = sentiment_result.error
            analysis.processed_at = timezone.now()
            analysis.save()
            
            logger.info(f"Successfully analyzed news {news_id} with {sentiment_result.provider}: {sentiment_result.label.value}")
            
        except Exception as e:
            logger.error(f"Error in AI analysis for news {news_id}: {str(e)}")
            
            # Fallback к простому анализу ключевых слов
            return AnalysisService._process_fallback_analysis(analysis, news, str(e))
        
        # Обновляем новость
        news.status = 'completed'
        news.save()
        
        # Если новость привязана к раунду, обновляем результат раунда
        game_round = news.game_rounds.filter(status='closed').first()
        if game_round:
            game_round.result = analysis.label
            game_round.save()
        
        return analysis
    
    @staticmethod
    def _process_mock_analysis(analysis: NewsAnalysis, news: News, mock_result: str) -> NewsAnalysis:
        """
        Обработка mock анализа для тестирования
        """
        analysis.status = 'processed'
        analysis.label = mock_result
        analysis.score = Decimal('0.7500')
        analysis.provider = 'mock'
        analysis.model_name = 'mock_analysis'
        analysis.confidence_score = Decimal('0.7500')
        analysis.processing_time = 0.1
        analysis.processed_at = timezone.now()
        analysis.save()
        
        # Обновляем новость
        news.status = 'completed'
        news.save()
        
        # Если новость привязана к раунду, обновляем результат раунда
        game_round = news.game_rounds.filter(status='closed').first()
        if game_round:
            game_round.result = mock_result
            game_round.save()
        
        return analysis
    
    @staticmethod
    def _process_fallback_analysis(analysis: NewsAnalysis, news: News, error_message: str) -> NewsAnalysis:
        """
        Fallback анализ на основе ключевых слов
        """
        # Простой анализ ключевых слов
        positive_words = ['success', 'growth', 'profit', 'gain', 'rise', 'up', 'positive', 'excellent', 'great', 'good']
        negative_words = ['loss', 'decline', 'fall', 'crash', 'down', 'negative', 'drop', 'terrible', 'awful', 'bad']
        
        title_lower = news.title.lower()
        content_lower = news.content.lower()
        text_to_analyze = f"{title_lower} {content_lower}"
        
        positive_count = sum(1 for word in positive_words if word in text_to_analyze)
        negative_count = sum(1 for word in negative_words if word in text_to_analyze)
        
        if positive_count > negative_count:
            label = 'positive'
            confidence = min(0.8, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            label = 'negative'
            confidence = min(0.8, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            # По умолчанию negative для большей непредсказуемости
            label = 'negative'
            confidence = 0.5
        
        analysis.status = 'processed'
        analysis.label = label
        analysis.score = Decimal(str(confidence))
        analysis.provider = 'fallback'
        analysis.model_name = 'keyword_analysis'
        analysis.confidence_score = Decimal(str(confidence))
        analysis.processing_time = 0.01
        analysis.error_message = f"AI analysis failed: {error_message}. Used fallback keyword analysis."
        analysis.processed_at = timezone.now()
        analysis.save()
        
        # Обновляем новость
        news.status = 'completed'
        news.save()
        
        # Если новость привязана к раунду, обновляем результат раунда
        game_round = news.game_rounds.filter(status='closed').first()
        if game_round:
            game_round.result = label
            game_round.save()
        
        logger.warning(f"Used fallback analysis for news {news.id}: {label} (confidence: {confidence})")
        
        return analysis
    
    @staticmethod
    def get_analysis_statistics() -> Dict[str, Any]:
        """
        Получить статистику анализа новостей
        
        Returns:
            Dict: Статистика анализа
        """
        from .sentiment_service import NewsSentimentService
        
        total_analyses = NewsAnalysis.objects.count()
        processed_analyses = NewsAnalysis.objects.filter(status='processed').count()
        failed_analyses = NewsAnalysis.objects.filter(status='failed').count()
        pending_analyses = NewsAnalysis.objects.filter(status='pending').count()
        
        # Статистика по провайдерам
        provider_stats = {}
        for analysis in NewsAnalysis.objects.filter(status='processed').exclude(provider=''):
            provider = analysis.provider
            if provider not in provider_stats:
                provider_stats[provider] = {'count': 0, 'avg_confidence': 0, 'avg_time': 0}
            
            provider_stats[provider]['count'] += 1
            if analysis.confidence_score:
                provider_stats[provider]['avg_confidence'] += float(analysis.confidence_score)
            if analysis.processing_time:
                provider_stats[provider]['avg_time'] += analysis.processing_time
        
        # Вычисляем средние значения
        for provider in provider_stats:
            count = provider_stats[provider]['count']
            if count > 0:
                provider_stats[provider]['avg_confidence'] /= count
                provider_stats[provider]['avg_time'] /= count
        
        # Статистика по тональности
        sentiment_stats = {
            'positive': NewsAnalysis.objects.filter(status='processed', label='positive').count(),
            'negative': NewsAnalysis.objects.filter(status='processed', label='negative').count(),
        }
        
        # Получаем статус OpenAI сервиса
        from .openai_sentiment_service import OpenAISentimentService
        openai_status = OpenAISentimentService.get_service_status()
        
        return {
            'total_analyses': total_analyses,
            'processed_analyses': processed_analyses,
            'failed_analyses': failed_analyses,
            'pending_analyses': pending_analyses,
            'provider_stats': provider_stats,
            'sentiment_stats': sentiment_stats,
            'openai_status': openai_status
        }


class RoundParticipationService:
    """
    Service for user interaction with rounds
    """
    
    @staticmethod
    def participate_in_round(user: CustomUser, round_id: int) -> Tuple[bool, str, Optional[dict]]:
        """
        User participation in a round with bonus accrual
        
        Args:
            user: User
            round_id: Round ID
            
        Returns:
            Tuple[bool, str, Optional[dict]]: (success, message, bonus_info)
        """
        try:
            with transaction.atomic():
                # Get round and check its status
                try:
                    game_round = GameRound.objects.select_for_update().get(id=round_id)
                except GameRound.DoesNotExist:
                    return False, "Round not found", None
                
                # Check that round is open
                if game_round.status != 'open':
                    return False, "Round is closed for participation", None
                
                # Check that round time has not expired
                if game_round.end_time <= timezone.now():
                    return False, "Round time has expired", None
                
                # Убираем проверку на единственное участие - теперь пользователь может участвовать многократно
                
                # Accrue participation bonus
                created, message, bonus = BonusService.check_round_participation_bonus(user, round_id)
                
                if created and bonus:
                    bonus_info = {
                        'bonus_id': bonus.id,
                        'amount': bonus.amount,
                        'type': bonus.bonus_type,
                        'description': bonus.description
                    }
                    
                    logger.info(f"User {user.username} successfully participated in round {round_id}")
                    return True, f"Successful participation in round! {message}", bonus_info
                else:
                    return False, f"Bonus accrual error: {message}", None
                
        except Exception as e:
            logger.error(f"Error during user {user.username} participation in round {round_id}: {str(e)}")
            return False, f"Internal error: {str(e)}", None
