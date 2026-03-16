import logging
import time
import openai
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

from .models import PlatformSettings

logger = logging.getLogger(__name__)


class SentimentLabel(Enum):
    """Метки тональности - только два варианта"""
    POSITIVE = "positive"
    NEGATIVE = "negative"


@dataclass
class SentimentResult:
    """Результат анализа тональности"""
    label: SentimentLabel
    confidence: float
    provider: str
    model: str
    processing_time: float
    raw_response: Optional[str] = None
    error: Optional[str] = None


class OpenAISentimentService:
    """
    Сервис для анализа тональности новостей с использованием OpenAI API
    """

    # Промпт для анализа тональности
    SENTIMENT_PROMPT = """
Проанализируй тональность следующей новости и определи, является ли она позитивной или негативной для рынка/экономики.

Заголовок: {title}
Содержание: {content}
Ссылка: {url}

Инструкции:
1. Внимательно прочитай заголовок и содержание новости
2. Определи общую тональность новости: позитивная или негативная
3. Учитывай контекст, эмоциональную окраску и влияние на рынок
4. Ответь ТОЛЬКО одним словом: "positive" или "negative"
5. Не добавляй никаких объяснений или дополнительного текста

Ответ:
"""

    @classmethod
    def analyze_sentiment(
        cls,
        title: str,
        content: str,
        url: str = ""
    ) -> SentimentResult:
        """
        Анализ тональности новости с помощью OpenAI API

        Args:
            title: Заголовок новости
            content: Содержание новости
            url: Ссылка на новость

        Returns:
            SentimentResult: Результат анализа
        """
        start_time = time.time()
        
        try:
            # Получаем настройки OpenAI
            settings = PlatformSettings.get_current()
            if not settings.openai_api_key:
                return SentimentResult(
                    label=SentimentLabel.NEGATIVE,
                    confidence=0.0,
                    provider="openai",
                    model="none",
                    processing_time=time.time() - start_time,
                    error="OpenAI API key not configured"
                )
            
            # Настраиваем клиент OpenAI

            client = openai.OpenAI(api_key=settings.openai_api_key)
            # Подготавливаем промпт

            prompt = cls.SENTIMENT_PROMPT.format(
                title=title[:200],  # Ограничиваем длину заголовка
                content=content[:1000],  # Ограничиваем длину контента
                url=url
            )
            
            # Отправляем запрос к OpenAI
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.openai_max_tokens,
                temperature=float(settings.openai_temperature),
                timeout=30
            )
            
            # Получаем ответ
            if response and response.choices:
                raw_response = response.choices[0].message.content.strip()
                
                # Парсим ответ
                label = cls._parse_sentiment_response(raw_response)
                confidence = cls._calculate_confidence(raw_response)
                processing_time = time.time() - start_time
                
                return SentimentResult(
                    label=label,
                    confidence=confidence,
                    provider="openai",
                    model=settings.openai_model,
                    processing_time=processing_time,
                    raw_response=raw_response
                )
            else:
                return SentimentResult(
                    label=SentimentLabel.NEGATIVE,
                    confidence=0.0,
                    provider="openai",
                    model=settings.openai_model,
                    processing_time=time.time() - start_time,
                    error="No response from OpenAI"
                )
                
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            return SentimentResult(
                label=SentimentLabel.NEGATIVE,
                confidence=0.0,
                provider="openai",
                model="none",
                processing_time=time.time() - start_time,
                error=f"Authentication error: {str(e)}"
            )
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {str(e)}")
            return SentimentResult(
                label=SentimentLabel.NEGATIVE,
                confidence=0.0,
                provider="openai",
                model="none",
                processing_time=time.time() - start_time,
                error=f"Rate limit error: {str(e)}"
            )
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return SentimentResult(
                label=SentimentLabel.NEGATIVE,
                confidence=0.0,
                provider="openai",
                model="none",
                processing_time=time.time() - start_time,
                error=f"API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI analysis: {str(e)}")
            return SentimentResult(
                label=SentimentLabel.NEGATIVE,
                confidence=0.0,
                provider="openai",
                model="none",
                processing_time=time.time() - start_time,
                error=f"Unexpected error: {str(e)}"
            )

    @classmethod
    def _parse_sentiment_response(cls, response: str) -> SentimentLabel:
        """
        Парсинг ответа OpenAI для определения тональности

        Args:
            response: Ответ OpenAI

        Returns:
            SentimentLabel: Определенная тональность
        """
        response = response.strip().lower()

        # Ищем ключевые слова в ответе
        if 'positive' in response:
            return SentimentLabel.POSITIVE
        elif 'negative' in response:
            return SentimentLabel.NEGATIVE

        # Если не нашли явных указаний, анализируем контекст
        positive_indicators = [
            'good', 'great', 'excellent', 'success', 'growth', 'profit', 
            'gain', 'rise', 'up', 'positive', 'optimistic', 'favorable', 
            'bullish', 'strong', 'record', 'breakthrough', 'achievement'
        ]
        negative_indicators = [
            'bad', 'terrible', 'awful', 'loss', 'decline', 'fall', 
            'crash', 'down', 'negative', 'pessimistic', 'unfavorable', 
            'crisis', 'bearish', 'weak', 'failure', 'drop', 'collapse'
        ]

        positive_count = sum(1 for word in positive_indicators if word in response)
        negative_count = sum(1 for word in negative_indicators if word in response)

        if positive_count > negative_count:
            return SentimentLabel.POSITIVE
        else:
            return SentimentLabel.NEGATIVE

    @classmethod
    def _calculate_confidence(cls, response: str) -> float:
        """
        Расчет уверенности в результате анализа

        Args:
            response: Ответ OpenAI

        Returns:
            float: Уверенность от 0.0 до 1.0
        """
        # Базовая уверенность
        base_confidence = 0.8

        # Увеличиваем уверенность если ответ четкий
        if any(word in response for word in ['definitely', 'clearly', 'obviously', 'certainly']):
            base_confidence += 0.1
        elif any(word in response for word in ['maybe', 'possibly', 'might', 'could']):
            base_confidence -= 0.1

        # Увеличиваем уверенность если есть обоснование
        if len(response) > 50:  # Длинный ответ обычно означает обоснование
            base_confidence += 0.05

        return min(1.0, max(0.0, base_confidence))

    @classmethod
    def test_connection(cls) -> Dict[str, Any]:
        """
        Тестирование подключения к OpenAI API

        Returns:
            Dict: Результат тестирования
        """
        test_title = "Company Reports Record Profits and Growth"
        test_content = "The company announced record-breaking quarterly profits with 25% revenue growth, exceeding all analyst expectations."
        test_url = "https://example.com/test"

        try:
            start_time = time.time()
            result = cls.analyze_sentiment(test_title, test_content, test_url)
            processing_time = time.time() - start_time

            return {
                'success': not result.error,
                'processing_time': processing_time,
                'response': result.raw_response,
                'error': result.error,
                'label': result.label.value if result.label else None,
                'confidence': result.confidence
            }

        except Exception as e:
            return {
                'success': False,
                'processing_time': 0.0,
                'response': None,
                'error': str(e),
                'label': None,
                'confidence': 0.0
            }

    @classmethod
    def get_service_status(cls) -> Dict[str, Any]:
        """
        Получить статус сервиса OpenAI

        Returns:
            Dict: Статус сервиса
        """
        settings = PlatformSettings.get_current()
        
        return {
            'provider': 'openai',
            'model': settings.openai_model,
            'api_key_configured': bool(settings.openai_api_key),
            'max_tokens': settings.openai_max_tokens,
            'temperature': float(settings.openai_temperature),
            'available': bool(settings.openai_api_key)
        }
