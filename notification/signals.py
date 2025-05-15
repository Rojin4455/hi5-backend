# notification/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Configure logging
logger = logging.getLogger(__name__)

# Import User model from accounts app
User = get_user_model()

@receiver(post_save, sender=User)
def create_user_notification(sender, instance, created, **kwargs):
    try:
        # Only create notifications for owner users
        if created and hasattr(instance, 'is_owner') and instance.is_owner:
            logger.info(f"Signal received for owner user {instance.email}. Created: {created}")
            
            # Import Notification model
            from .models import Notification
            
            # Find admin users
            admin_users = User.objects.filter(is_staff=True)
            logger.info(f"Found {admin_users.count()} admin users")

            # Create notifications for each admin
            for admin in admin_users:
                notification = Notification.objects.create(
                    user=admin, 
                    message=f"New owner user {instance.email} has been created",
                    created_user = instance.id,
                )
            
            # Send WebSocket notification
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'admin_notifications', 
                {
                    'type': 'send_notification',
                    'id': notification.id,
                    'message': f"New owner user {instance.email} has been created"
                }
            )
            logger.info("Notification created and WebSocket message sent")
    
    except Exception as e:
        logger.error(f"Error in user creation signal: {str(e)}")