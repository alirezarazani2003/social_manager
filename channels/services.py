import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from telegram.error import TelegramError
from channels.models import Channel

def verify_telegram_channel(username: str):
    """
    بررسی می‌کند که آیا ربات تلگرام توانایی ارسال پیام در کانال را دارد یا خیر.
    پیام تست ارسال می‌کند و نتیجه را برمی‌گرداند.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    test_message = "در حال بررسی دسترسی ربات برای ارسال پست..."
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(api_url, json={
            "chat_id": username,
            "text": test_message
        }, timeout=5)

        if response.status_code == 200:
            return True, username
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


from telegram import Bot, InputMediaPhoto, InputMediaVideo
from telegram.error import TelegramError
from channels.models import Channel

def send_message_to_channel(channel: Channel, text: str = "", files: list = None):
    """
    فایل‌ها باید لیستی از دیکشنری‌های شامل این موارد باشند:
    [
        {"path": "/media/path/to/image.jpg", "caption": "توضیح"},
        {"path": "/media/another.png", "caption": ""},
        ...
    ]
    """
    bot_token = channel.bot_token  # فرض: در مدل Channel ذخیره شده
    chat_id = channel.telegram_chat_id  # فرض: در وریفای ذخیره شده

    bot = Bot(token=bot_token)

    try:
        if not files:
            # فقط پیام متنی
            bot.send_message(chat_id=chat_id, text=text)
            return True, ""

        elif len(files) == 1:
            # فقط یک فایل همراه با کپشن
            file_info = files[0]
            path = file_info["path"]
            caption = file_info.get("caption", "")

            if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'), caption=caption or text)
            elif path.lower().endswith(('.mp4', '.mov', '.mkv')):
                bot.send_video(chat_id=chat_id, video=open(path, 'rb'), caption=caption or text)
            else:
                bot.send_document(chat_id=chat_id, document=open(path, 'rb'), caption=caption or text)
            return True, ""

        else:
            # چند فایل: ارسال به صورت آلبوم (photo/video only)
            media_group = []
            for i, f in enumerate(files):
                path = f["path"]
                caption = f.get("caption", "") if i == 0 else None  # فقط اولین عکس کپشن داشته باشد

                if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    media = InputMediaPhoto(media=open(path, 'rb'), caption=caption)
                elif path.lower().endswith(('.mp4', '.mov', '.mkv')):
                    media = InputMediaVideo(media=open(path, 'rb'), caption=caption)
                else:
                    continue  # فایل غیرقابل پشتیبانی برای آلبوم

                media_group.append(media)

            if not media_group:
                return False, "هیچ فایل تصویری یا ویدیویی قابل ارسال نبود."
            bot.send_media_group(chat_id=chat_id, media=media_group)
            return True, ""

    except TelegramError as e:
        return False, str(e)
