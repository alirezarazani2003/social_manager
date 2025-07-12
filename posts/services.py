import requests
from django.conf import settings

def send_telegram_message(chat_id: str, text: str):
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    response = requests.post(url, data=payload)
    return response.json()