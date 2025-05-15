import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from notification.models import Notification
from django.core.serializers import serialize
from datetime import datetime


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Add the client to the admin notifications group
        await self.channel_layer.group_add('admin_notifications', self.channel_name)
        
        # Accept the WebSocket connection
        await self.accept()
        
        # Fetch and send existing notifications
        await self.send_existing_notifications()

    async def disconnect(self, close_code):
        # Remove the client from the admin notifications group
        await self.channel_layer.group_discard('admin_notifications', self.channel_name)

    @database_sync_to_async
    def get_existing_notifications(self):
        # Fetch unread notifications ordered by most recent
        notifications = Notification.objects.all().values(
            'id', 'message', 'created_at', 'is_read'
        )
        # Convert created_at datetime to string
        return [
            {
                **notification,
                'created_at': notification['created_at'].strftime('%Y-%m-%dT%H:%M:%S')  # ISO 8601 format
            }
            for notification in notifications
        ]


    async def send_existing_notifications(self):
        # Retrieve existing notifications
        notifications = await self.get_existing_notifications()
        
        # Send notifications to the client
        await self.send(text_data=json.dumps({
            'type': 'existing_notifications',
            'notifications': notifications
        }))

    async def send_notification(self, event):
        # Handle incoming notifications from the group
        message = event['message']
        new_notification = {
            'id': event.get('id', None),
            'message': message,
            'is_read': False,
            'created_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')  # Default to now
        }
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': new_notification
        }))