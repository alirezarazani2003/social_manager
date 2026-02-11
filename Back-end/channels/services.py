import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from telegram.error import TelegramError
import asyncio
from telegram import InputMediaPhoto, InputMediaVideo
import json


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
    token = settings.BALE_BOT_TOKEN
    test_message = "در حال بررسی دسترسی ربات برای ارسال پست..."
    api_url = f"https://tapi.bale.ai/bot{token}/sendMessage"

    try:
        response = requests.post(api_url, json={
            "chat_id": username,
            "text": test_message
        }, timeout=5)

        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            chat_info = result.get("chat", {})

            return True, {
                "chat_id": chat_info.get("id", username),
                "username": chat_info.get("username", username),
            }
        else:
            error_text = response.json().get("description", "خطای ناشناخته از سمت بله")
            return False, error_text

    except requests.exceptions.RequestException as e:
        return False, f"خطا در اتصال به سرور بله: {str(e)}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}"


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
    platform = channel.platform
    if platform == "telegram":
        return send_message_telegram(channel, text, files)
    elif platform == "bale":
        return send_message_bale(channel, text, files)
    else:
        return False, _("پلتفرم ناشناخته است.")



def send_message_telegram(channel, text: str = "", files: list = None):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = channel.platform_channel_id
    base_url = f"https://api.telegram.org/bot{token}"

    try:
        if not files:
            url = f"{base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text or " ",
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            response = requests.post(url, data=data, timeout=60)

        elif len(files) == 1:
            f_info = files[0]
            path = f_info["path"]
            caption = f_info.get("caption", "") or text

            with open(path, "rb") as f:
                if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    url = f"{base_url}/sendPhoto"
                    files_payload = {"photo": f}
                elif path.lower().endswith(('.mp4', '.mov', '.mkv', '.avi', '.webm')):
                    url = f"{base_url}/sendVideo"
                    files_payload = {"video": f}
                elif path.lower().endswith(('.oga', '.ogg')): 
                    url = f"{base_url}/sendVoice"
                    files_payload = {"voice": f}
                else:
                    url = f"{base_url}/sendDocument"
                    files_payload = {"document": f}

                data = {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "MarkdownV2"
                }
                response = requests.post(url, data=data, files=files_payload, timeout=120)

        else:
            media = []
            files_payload = {}

            for i, f_info in enumerate(files[:10]):
                path = f_info["path"]
                caption = f_info.get("caption", "") if i == 0 else ""
                field_name = f"file{i}"

                if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    media_type = "photo"
                elif path.lower().endswith(('.mp4', '.mov', '.mkv', '.avi', '.webm')):
                    media_type = "video"
                else:
                    continue

                media.append({
                    "type": media_type,
                    "media": f"attach://{field_name}",
                    "caption": caption if i == 0 else "",
                    "parse_mode": "MarkdownV2"
                })

                files_payload[field_name] = open(path, "rb")

            if not media:
                return False, "هیچ فایل تصویری یا ویدیویی معتبری برای آلبوم پیدا نشد."

            url = f"{base_url}/sendMediaGroup"
            data = {
                "chat_id": chat_id,
                "media": json.dumps(media, ensure_ascii=False)
            }
            response = requests.post(url, data=data, files=files_payload, timeout=180)

        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("ok"):
                return True, ""
            else:
                error_desc = resp_json.get("description", "خطای نامشخص تلگرام")
                return False, f"Telegram API Error: {error_desc}"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"

    except requests.exceptions.Timeout:
        return False, "Timeout: ارسال به تلگرام بیش از حد طول کشید."
    except FileNotFoundError as e:
        return False, f"فایل پیدا نشد: {e}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}"
    finally:
        if 'files_payload' in locals():
            for f in files_payload.values():
                try:
                    f.close()
                except:
                    pass

def send_message_bale(channel , text:str="" , files:list=None):
    token = settings.BALE_BOT_TOKEN
    chat_id = channel.platform_channel_id
    try:
        if not files:
            url =f"https://tapi.bale.ai/bot{token}/sendMessage"
            data={
                "chat_id": chat_id,
                "text": text
            }
            response=requests.post(url , data)
        elif len(files) == 1 :
            f_info=files[0]
            path=f_info["path"]
            caption=f_info.get("caption" , "")
            if path.lower().endswith((".png" , ".jpg" , ".gif" )):
                url=f"https://tapi.bale.ai/bot{token}/sendPhoto"
                data={
                    "caption": caption or text,
                    "chat_id":chat_id
                }
                with open(path, "rb") as f: 
                    file_data = {"photo": f}
                    response = requests.post(url, data=data, files=file_data)
            elif path.lower().endswith((".mp4" , ".mov" , ".avi" )):
                url=f"https://tapi.bale.ai/bot{token}/sendVideo"
                data={
                    "text":text,
                    "chat_id":chat_id
                }
                with open(path, "rb") as f: 
                    file_data = {"video": f} 
                    response = requests.post(url, data=data, files=file_data)
            else :
                url=f"https://tapi.bale.ai/bot{token}/sendDocument"
                data={
                    "text":text,
                    "chat_id":chat_id
                }
                with open(path, "rb") as f: 
                    file_data = {"document": f} 
                    response = requests.post(url, data=data, files=file_data)
        elif len(files) > 1:
            media = []
            files_payload = {}

            for i, f_info in enumerate(files):
                path = f_info["path"]
                caption = f_info.get("caption") if i == 0 else None
                field_name = f"file{i}"

                if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    media.append({
                        "type": "photo",
                        "media": f"attach://{field_name}",
                        "caption": caption
                    })
                elif path.lower().endswith(('.mp4', '.mov', '.mkv')):
                    media.append({
                        "type": "video",
                        "media": f"attach://{field_name}",
                        "caption": caption
                    })
                else:
                    continue  

                files_payload[field_name] = open(path, "rb")

            url = f"https://tapi.bale.ai/bot{token}/sendMediaGroup"
            data = {
                "chat_id": chat_id,
                "media": json.dumps(media, ensure_ascii=False)
            }

            response = requests.post(url, data=data, files=files_payload)

        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("ok"):
                return True, ""
            else:
                return False, resp_json.get("description", "خطای نامشخص از بله.")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
        
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}"