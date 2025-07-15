import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from telegram.error import TelegramError
import asyncio

def verify_telegram_channel(username: str):
    token = settings.TELEGRAM_BOT_TOKEN
    test_message = "در حال بررسی دسترسی ربات برای ارسال پست..."
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(api_url, json={
            "chat_id": username,
            "text": test_message
        }, timeout=5)

        if response.status_code == 200:
            data = response.json()
            chat_info = data["result"]["chat"]
            return True, {
                "chat_id": chat_info["id"],  # -1001234567890
                "username": chat_info.get("username"),
            }
        else:
            error_text = response.json().get("description", "خطای ناشناخته از سمت تلگرام")
            return False, error_text

    except requests.exceptions.RequestException as e:
        return False, f"خطا در اتصال به سرور تلگرام: {str(e)}"


def verify_bale_channel(username: str):
    """
    بررسی اتصال ربات بله به کانال.
    فعلاً پیاده‌سازی نشده است.
    """
    return False, _("فعلاً اتصال به بله پیاده‌سازی نشده است.")


def verify_channel(platform: str, username: str):
    """
    سوئیچ اعتبارسنجی کانال بر اساس پلتفرم.
    """
    if platform == "telegram":
        return verify_telegram_channel(username)
    elif platform == "bale":
        return verify_bale_channel(username)
    else:
        return False, _("پلتفرم ناشناخته است.")


def send_message_to_channel(channel, text: str = "", files: list = None):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = channel.platform_channel_id
    bot = Bot(token=bot_token)

    async def _send():
        try:
            if not files:
                await bot.send_message(chat_id=chat_id, text=text,read_timeout=60)
                return True, ""

            elif len(files) == 1:
                file_info = files[0]
                path = file_info["path"]
                caption = file_info.get("caption", "")

                if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    await bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'), caption=caption or text,read_timeout=60)
                elif path.lower().endswith(('.mp4', '.mov', '.mkv')):
                    await bot.send_video(chat_id=chat_id, video=open(path, 'rb'), caption=caption or text,read_timeout=60)
                else:
                    await bot.send_document(chat_id=chat_id, document=open(path, 'rb'), caption=caption or text,read_timeout=60)
                return True, ""

            else:
                media_group = []
                for i, f in enumerate(files):
                    path = f["path"]
                    caption = f.get("caption", "") if i == 0 else None

                    if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                        media = InputMediaPhoto(media=open(path, 'rb'), caption=caption)
                    elif path.lower().endswith(('.mp4', '.mov', '.mkv')):
                        media = InputMediaVideo(media=open(path, 'rb'), caption=caption)
                    else:
                        continue
                    media_group.append(media)

                if not media_group:
                    return False, "هیچ فایل تصویری یا ویدیویی قابل ارسال نبود."

                await bot.send_media_group(chat_id=chat_id, media=media_group,read_timeout=60)
                return True, ""

        except TelegramError as e:
            return False, f"TelegramError: {str(e)}"
        except Exception as e:
            return False, f"{type(e).__name__}: {str(e)}"

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            result = asyncio.ensure_future(_send())
        else:
            result = loop.run_until_complete(_send())
        return result
    except Exception as e:
        return False, f"LoopError: {type(e).__name__}: {str(e)}"
