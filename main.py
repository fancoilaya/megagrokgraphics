import os
import threading
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from telegram.ext import Updater
from handlers.commands import get_handlers
from handlers.posting import generate_and_post

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POST_INTERVAL = int(os.getenv("POST_INTERVAL_HOURS", "2"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"status": "ok"})

def scheduler_job():
    generate_and_post(TELEGRAM_CHAT_ID, interval_hours=POST_INTERVAL)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduler_job, "interval", hours=POST_INTERVAL)
    scheduler.start()

def start_telegram():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    for handler in get_handlers():
        dp.add_handler(handler)

    updater.start_polling()

# Start everything
threading.Thread(target=start_scheduler, daemon=True).start()
threading.Thread(target=start_telegram, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
