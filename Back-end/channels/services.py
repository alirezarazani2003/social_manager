import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from telegram.error import TelegramError
import asyncio
from telegram import InputMediaPhoto, InputMediaVideo, InputMedia
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
                "chat_id": chat_info.get("id", username),  # در بله معمولاً id داده نمی‌شود، پس fallback به username
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
    platform = channel.platform  # مثلاً 'telegram' یا 'bale'
    if platform == "telegram":
        return send_message_telegram(channel, text, files)
    elif platform == "bale":
        return send_message_bale(channel, text, files)
    else:
        return False, _("پلتفرم ناشناخته است.")



def send_message_telegram(channel, text: str = "", files: list = None):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = channel.platform_channel_id
    bot = Bot(token=bot_token)

    async def _send():
        try:
            if not files:
                await bot.send_message(chat_id=chat_id, text=text, read_timeout=60)
                return True, ""

            elif len(files) == 1:
                file_info = files[0]
                path = file_info["path"]
                caption = file_info.get("caption", "")

                if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    with open(path, 'rb') as f:
                        await bot.send_photo(chat_id=chat_id, photo=f, caption=caption or text, read_timeout=60)
                elif path.lower().endswith(('.mp4', '.mov', '.mkv')):
                    with open(path, 'rb') as f:
                        await bot.send_video(chat_id=chat_id, video=f, caption=caption or text, read_timeout=60)
                else:
                    with open(path, 'rb') as f:
                        await bot.send_document(chat_id=chat_id, document=f, caption=caption or text, read_timeout=60)
                return True, ""

            else:
                media_group = []
                for i, f_info in enumerate(files):
                    path = f_info["path"]
                    caption = f_info.get("caption", "") if i == 0 else None

                    if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                        media_group.append(InputMediaPhoto(media=open(path, 'rb'), caption=caption))
                    elif path.lower().endswith(('.mp4', '.mov', '.mkv')):
                        media_group.append(InputMediaVideo(media=open(path, 'rb'), caption=caption))
                    else:
                        continue

                if not media_group:
                    return False, "هیچ فایل تصویری یا ویدیویی قابل ارسال نبود."

                await bot.send_media_group(chat_id=chat_id, media=media_group, read_timeout=60)
                return True, ""

        except TelegramError as e:
            return False, f"TelegramError: {str(e)}"
        except Exception as e:
            return False, f"{type(e).__name__}: {str(e)}"

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError("Event loop already running")
        else:
            if not loop:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            result = loop.run_until_complete(_send())
            return result
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(_send())
    except Exception as e:
        return False, f"LoopError: {type(e).__name__}: {str(e)}"
    


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
            # media_group: list[InputMedia] = []
            # for i, f_info in enumerate(files):
            #     path = f_info["path"]
            #     caption = f_info.get("caption", "") if i == 0 else None

            #     if path.lower().endswith(('.jpg', '.jpeg', '.png')):
            #         media_group.append(InputMediaPhoto(media=open(path, 'rb'), caption=caption))
            #     elif path.lower().endswith(('.mp4', '.mov', '.mkv')):
            #         media_group.append(InputMediaVideo(media=open(path, 'rb'), caption=caption))
            #     else:
            #         continue

            # if not media_group:
            #     return False, "هیچ فایل تصویری یا ویدیویی قابل ارسال نبود."

            # response=requests.post(url=f"https://tapi.bale.ai/bot{token}/sendMediaGroup", data={"chat_id": chat_id, "media": media_group})

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
