# main.py
import os
import threading
import asyncio
import logging
from datetime import datetime

from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

# telegram async v20
from telegram.ext import ApplicationBuilder

from handlers.commands import get_handlers
from handlers.posting import generate_and_post

# --------------------------
# Env and config
# --------------------------
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", "2"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_CHAT_ID or not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_CHAT_ID or TELEGRAM_BOT_TOKEN")

# --------------------------
# Logging
# --------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("megagrok-main")

app = Flask("megagrok_graphics_bot")

@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "service": "megagrok_graphics_bot",
        "time": datetime.utcnow().isoformat() + "Z"
    })

# --------------------------
# Scheduler job
# --------------------------
def scheduler_job():
    logger.info("Running scheduled generation for chat %s", TELEGRAM_CHAT_ID)
    ok, info = generate_and_post(TELEGRAM_CHAT_ID, POST_INTERVAL_HOURS)
    if ok:
        logger.info("Scheduled poster posted: %s", info)
    else:
        logger.error("Scheduled generation failed: %s", info)

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(scheduler_job, 'interval', hours=POST_INTERVAL_HOURS)
    scheduler.start()
    logger.info("Scheduler started: every %s hours", POST_INTERVAL_HOURS)

    try:
        logger.info("Running initial scheduled job...")
        scheduler_job()
    except Exception as e:
        logger.exception("Initial scheduled job failed: %s", e)

# --------------------------
# Telegram: async PTB20 in background thread
# --------------------------
async def run_telegram_async():
    """Build and run the async Telegram application (blocking call inside asyncio)."""
    app_builder = ApplicationBuilder().token(BOT_TOKEN)
    application = app_builder.build()

    # register handlers
    for handler in get_handlers():
        application.add_handler(handler)

    logger.info("Starting Telegram polling (async)")
    # This will run until stopped - run_polling is high-level convenience
    await application.run_polling()

def start_telegram_thread():
    # Start asyncio loop in a thread
    def _run():
        asyncio.run(run_telegram_async())
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    logger.info("Telegram polling thread started")

# --------------------------
# Start everything
# --------------------------
if __name__ == "__main__":
    # Scheduler thread
    threading.Thread(target=start_scheduler, daemon=True).start()

    # Telegram thread (async)
    start_telegram_thread()

    # Flask app (Render expects HTTP server)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
