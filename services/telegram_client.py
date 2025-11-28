# services/telegram_client.py
import os
import io
import logging
import requests

logger = logging.getLogger(__name__)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment")

def tg_send_photo(chat_id: str, image_bytes: bytes, filename: str, caption: str = None) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {"photo": (filename, io.BytesIO(image_bytes), "image/png")}
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    try:
        r = requests.post(url, data=data, files=files, timeout=60)
        r.raise_for_status()
        j = r.json()
        if not j.get("ok"):
            logger.error("Telegram API error: %s", j)
            return False
        return True
    except Exception as e:
        logger.exception("Failed to send photo to Telegram: %s", e)
        return False
