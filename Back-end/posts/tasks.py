# posts/tasks.py
import logging
from celery import shared_task
from .models import Post
from channels.services import send_message_to_channel
from django.utils import timezone

task_logger = logging.getLogger('posts.task')

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_post_task(self, post_id):
    task_logger.info(f"send_post_task received with post_id: {post_id}")

    try:
        post = Post.objects.get(id=post_id)

        if post.status != 'pending':
            task_logger.warning(f"Post {post_id} skipped: status is '{post.status}'")
            return f"Skipped: Post is in status '{post.status}'"

        channels = post.channels.all()
        if not channels.exists():
            task_logger.warning(f"Post {post_id} has no channels")
            return "No channels found"

        attachments = post.attachments.all()
        text = post.content

        results = []
        successful_sends = 0

        for channel in channels:
            try:
                if post.types == 'text':
                    success, error = send_message_to_channel(channel, text)
                elif post.types == 'media':
                    if not attachments.exists():
                        result = f"Channel {channel.username}: No media attachment found"
                        results.append(result)
                        task_logger.warning(f"Post {post_id} - {result}")
                        continue

                    files = []
                    for i, attach in enumerate(attachments):
                        files.append({
                            "path": attach.file.path,
                            "caption": text if i == 0 else ""
                        })

                    success, error = send_message_to_channel(channel, None, files=files)
                else:
                    result = f"Channel {channel.username}: Unsupported post type"
                    results.append(result)
                    task_logger.warning(f"Post {post_id} - {result}")
                    continue

                if success:
                    results.append(f"Channel {channel.username}: Sent successfully")
                    successful_sends += 1
                    task_logger.info(f"Post {post_id} sent successfully to {channel.platform}:@{channel.username}")
                else:
                    results.append(f"Channel {channel.username}: Failed - {error}")
                    task_logger.error(f"Failed to send post {post_id} to {channel.platform}:@{channel.username}: {error}")

            except Exception as channel_error:
                error_msg = f"Channel {channel.username}: Error - {str(channel_error)}"
                results.append(error_msg)
                task_logger.error(f"Error sending post {post_id} to {channel.platform}: {channel_error}")

        if successful_sends > 0:
            post.status = 'sent'
            post.sent_at = timezone.now()
        else:
            post.status = 'failed'

        post.error_message = "; ".join(results)
        post.save()

        if post.status == 'sent':
            task_logger.info(f"Post {post_id} sent successfully to {successful_sends}/{len(channels)} channels")
        else:
            task_logger.error(f"Post {post_id} failed to send to all {len(channels)} channels")

        return "; ".join(results)

    except Post.DoesNotExist:
        task_logger.error(f"Post {post_id} does not exist")
        return "Post does not exist"

    except Exception as exc:
        task_logger.error(f"Retrying send_post_task for post {post_id}: {exc}")
        raise self.retry(exc=exc)