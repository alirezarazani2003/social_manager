from celery import shared_task
from .models import Post
from channels.services import send_message_to_channel 
from django.utils import timezone

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_telegram_task(self, post_id):
    try:
        post = Post.objects.get(id=post_id)

        # ✅ بررسی وضعیت پست: فقط اگر هنوز pending هست ادامه بده
        if post.status != 'pending':
            return f"Skipped: Post is in status '{post.status}'"

        channels = post.channels.all()
        if not channels.exists():
            return "No channels found"

        attachments = post.attachments.all()
        text = post.content

        results = []
        for channel in channels:
            try:
                if post.types == 'text':
                    success, error = send_message_to_channel(channel, text)
                elif post.types == 'media':
                    if not attachments.exists():
                        results.append(f"Channel {channel.username}: No media attachment found")
                        continue

                    files = []
                    for i, attach in enumerate(attachments):
                        files.append({
                            "path": attach.file.path,
                            "caption": text if i == 0 else ""
                        })

                    success, error = send_message_to_channel(channel, None, files=files)
                else:
                    results.append(f"Channel {channel.username}: Unsupported post type")
                    continue

                if success:
                    results.append(f"Channel {channel.username}: Sent successfully")
                else:
                    results.append(f"Channel {channel.username}: Failed - {error}")

            except Exception as channel_error:
                results.append(f"Channel {channel.username}: Error - {str(channel_error)}")

        successful_sends = [result for result in results if "Sent successfully" in result]

        if successful_sends:
            post.status = 'sent'
            post.sent_at = timezone.now()
            post.error_message = "; ".join(results)
        else:
            post.status = 'failed'
            post.error_message = "; ".join(results)

        post.save()
        return "; ".join(results)

    except Post.DoesNotExist:
        return "Post does not exist"

    except Exception as exc:
        raise self.retry(exc=exc)
    

