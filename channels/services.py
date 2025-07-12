import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import httpx


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


def send_message_to_channel(channel, text):
    """
    ارسال پیام به کانال بر اساس پلتفرم.
    """
    if channel.platform == 'telegram':
        try:
            token = settings.TELEGRAM_BOT_TOKEN
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            response = httpx.post(url, data={
                "chat_id": channel.platform_channel_id or channel.username,
                "text": text
            }, timeout=10)

            if response.status_code == 200:
                return True, None
            else:
                return False, f"خطای تلگرام: {response.text}"
        except Exception as e:
            return False, str(e)

    elif channel.platform == 'bale':
        return False, _("ارسال پیام به بله هنوز پیاده‌سازی نشده است.")
    
    else:
        return False, _("پلتفرم ناشناخته است.")
