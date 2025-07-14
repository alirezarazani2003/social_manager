# posts/tasks.py

from celery import shared_task
from .models import Post
from django.utils.timezone import now
import requests
from django.conf import settings

@shared_task
def send_post_task(post_id):
    try:
        post = Post.objects.select_related('channel').get(id=post_id)
        channel = post.channel
        bot_token = channel.telegram_bot_token  # فیلدی که در مدل Channel داری
        chat_id = channel.telegram_chat_id     # فیلدی که در مدل Channel داری

        # ساخت پیام و URL ارسال
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": post.text
        }

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            post.is_sent = True
            post.sent_at = now()
            post.error_message = None
        else:
            post.is_sent = False
            post.error_message = f"Telegram API error: {response.text}"

    except Exception as e:
        post = Post.objects.get(id=post_id)
        post.is_sent = False
        post.error_message = str(e)

    post.save()
