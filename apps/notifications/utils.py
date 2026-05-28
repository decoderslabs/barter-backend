import logging
import json
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_notification(user_id, notification_type, title, body, deep_link=None, send_email=False):
    """
    Send notification via Firebase FCM and optionally SendGrid email.
    """
    from .models import Notification
    from apps.users.models import User

    try:
        # Save to DB
        notification = Notification.objects.create(
            user_id=user_id,
            type=notification_type,
            title=title,
            body=body,
            deep_link=deep_link or ''
        )
        
        # Send FCM push
        try:
            send_fcm_notification(user_id, title, body, deep_link)
        except Exception as e:
            logger.error(f"FCM send failed: {e}")
        
        # Send email if requested
        if send_email:
            try:
                send_email_notification(user_id, notification_type, title, body)
            except Exception as e:
                logger.error(f"Email send failed: {e}")
        
        logger.info(f"Notification created: {title} for user {user_id}")
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        return None


def send_fcm_notification(user_id, title, body, deep_link=None):
    """Send push notification via Firebase FCM"""
    try:
        import firebase_admin
        from firebase_admin import messaging
        
        if not firebase_admin._apps:
            cred = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
            firebase_admin.initialize_app(cred)
        
        from apps.users.models import User
        user = User.objects.get(id=user_id)
        
        # Get user's FCM token (you'd need to store this in User model)
        fcm_token = getattr(user, 'fcm_token', None)
        if not fcm_token:
            return
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={'deep_link': deep_link or ''},
            token=fcm_token,
        )
        
        response = messaging.send(message)
        logger.info(f"FCM sent: {response}")
    except Exception as e:
        logger.error(f"FCM error: {e}")


def send_email_notification(user_id, notification_type, title, body):
    """Send email via SendGrid"""
    from apps.users.models import User
    user = User.objects.get(id=user_id)
    
    # Simple email for now - can be enhanced with templates
    send_mail(
        subject=f'Barter - {title}',
        message=body,
        from_email='noreply@barter.so',
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_bulk_notifications(user_ids, notification_type, title, body, deep_link=None):
    """Send notification to multiple users"""
    notifications = []
    for user_id in user_ids:
        notif = send_notification(user_id, notification_type, title, body, deep_link)
        if notif:
            notifications.append(notif)
    return notifications
