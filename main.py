# main.py

import os
import threading
import asyncio
import logging
from datetime import datetime

from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

# Telegram (PTB v20 async)
from telegram.ext import ApplicationBuilder

# Local modules
from handlers.commands import get_handlers
from handlers.posting import generate_and_post


# -------------------------------------------------
# Environment & Config
# -------------------------------------------------

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", "2"))

if not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

if not TELEGRAM_CHAT_ID:
    raise RuntimeError("Missing TELEGRAM_CHAT_ID")


# -------------------------------------------------
# Logging
# -------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("megagrok-main")


# -------------------------------------------------
# Flask App (Render requires HTTP server)
# -------------------------------------------------

app = Flask("megagrok_graphics_bot")


@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "service": "megagrok_graphics_bot",
        "time": datetime.utcnow().isoformat() + "Z"
    })


# -------------------------------------------------
# Scheduler Job
# -------------------------------------------------

def scheduler_job():
    logger.info("Running scheduled MegaGrok poster job...")
    ok, info = generate_and_post(TELEGRAM_CHAT_ID, POST_INTERVAL_HOURS)

    if ok:
        logger.info(f"Scheduled poster posted: {info}")
    else:
        logger.error(f"Scheduled poster FAILED: {info}")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(scheduler_job, "interval", hours=POST_INTERVAL_HOURS)
    scheduler.start()

    logger.info(f"Scheduler started | Interval: {POST_INTERVAL_HOURS}h")

    # Run immediately on boot
    try:
        scheduler_job()
    except Exception as e:
        logger.exception(f"Initial scheduled job failed: {e}")


# -------------------------------------------------
# Telegram Bot: Async PTB20 in background thread
# -------------------------------------------------

async def run_telegram_async():
    """Runs PTB 20+ asynchronous Telegram bot."""
    logger.info("Initializing Telegram bot...")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    for handler in get_handlers():
        application.add_handler(handler)

    logger.info("Starting Telegram polling...")
    await application.run_polling()


def start_telegram_thread():
    """Launches PTB20 asyncio loop inside a background thread."""

    def _run():
        asyncio.run(run_telegram_async())

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    logger.info("Telegram background thread started.")


# -------------------------------------------------
# Gunicorn-Compatible Initialization (Flask 3.x)
# -------------------------------------------------

@app.before_serving
def init_services():
    """
    Flask 3.x replacement for before_first_request.
    Runs once per Gunicorn worker.
    """

    logger.info("Flask worker is starting background services...")

    # Start scheduler in background
    threading.Thread(target=start_scheduler, daemon=True).start()

    # Start Telegram bot in background
    start_telegram_thread()

    logger.info("All background services started successfully.")


# -------------------------------------------------
# Local Development Mode (python main.py)
# -------------------------------------------------

if __name__ == "__main__":
    # Start scheduler
    threading.Thread(target=start_scheduler, daemon=True).start()

    # Start Telegram bot
    start_telegram_thread()

    # Start Flask dev server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
