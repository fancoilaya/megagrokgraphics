import os
import requests
import io

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def tg_send_photo(chat_id, image_bytes, filename, caption=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {"photo": (filename, io.BytesIO(image_bytes), "image/png")}
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption

    r = requests.post(url, data=data, files=files)
    return r.status_code == 200
