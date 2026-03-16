import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone


logger = logging.getLogger(__name__)
User = get_user_model()


class RoundNotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer для уведомлений о новых раундах и их обновлениях
    """
    
    async def connect(self):
        """Подключение к WebSocket"""
        self.group_name = 'round_notifications'
        

        
        # Присоединяемся к группе уведомлений
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        

        logger.info(f"User {self.scope['user'].username} connected to round notifications")

    async def disconnect(self, close_code):
        """Отключение от WebSocket"""
        # Покидаем группу уведомлений
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        
        if self.scope.get("user"):
            logger.info(f"User {self.scope['user'].username} disconnected from round notifications")

    async def receive(self, text_data):
        """Обработка сообщений от клиента"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Отвечаем на ping для поддержания соединения
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))


        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def round_notification(self, event):
        """Отправка уведомления о раунде"""
        notification_type = event.get('notification_type', 'round_updated')
        
        await self.send(text_data=json.dumps({
            'type': notification_type,
            'round': event['round_data'],
            'timestamp': event['timestamp']
        }))


