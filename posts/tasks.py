from celery import shared_task
from .models import Post
from channels.services import send_message_to_channel
from django.utils import timezone

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_post_task(self, post_id):
    try:
        post = Post.objects.get(id=post_id)
        if post.status == 'sent':
            return "Already sent"

        attachments = post.attachments.all()
        text = post.content

        if post.types == 'text':
            success, error = send_message_to_channel(post.channel, text)

        elif post.types == 'media':
            if not attachments.exists():
                return "No media attachment found"

            files = []
            for i, attach in enumerate(attachments):
                files.append({
                    "path": attach.file.path,
                    "caption": text if i == 0 else "" 
                })

            success, error = send_message_to_channel(post.channel, None, files=files)

        else:
            return "Unsupported post type"

        if success:
            post.status = 'sent'
            post.sent_at = timezone.now()
            post.save()
            return "Sent successfully"
        else:
            post.status = 'failed'
            post.error_message = error
            post.save()
            return f"Failed: {error}"

    except Post.DoesNotExist:
        return "Post does not exist"

    except Exception as exc:
        raise self.retry(exc=exc)
