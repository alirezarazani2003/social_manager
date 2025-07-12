from celery import shared_task
from .models import Post
from .services import send_post_to_channel

@shared_task
def send_post_task(post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return

    post.status = 'sending'
    post.save()

    success, error = send_post_to_channel(post)

    if success:
        post.status = 'sent'
        post.sent_at = timezone.now()
        post.error_message = ''
    else:
        post.status = 'failed'
        post.error_message = error
    post.save()
