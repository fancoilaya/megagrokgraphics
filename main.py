import os
import threading
import logging
from flask import Flask, jsonify
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from telegram.ext import Updater

# Local project imports
from handlers.commands import get_handlers
from handlers.posting import generate_and_post

# --------------------------
# Env Variables
# --------------------------
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", "2"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_CHAT_ID or not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_CHAT_ID or TELEGRAM_BOT_TOKEN in environment variables")

# --------------------------
# Logging
# --------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("megagrok-main")

# --------------------------
# Flask App (Health Check)
# --------------------------
app = Flask("megagrok_graphics_bot")

@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "service": "megagrok_graphics_bot",
        "time": datetime.utcnow().isoformat() + "Z"
    })

# --------------------------
# SCHEDULER TASK
# --------------------------
def scheduler_job():
    """Called automatically every POST_INTERVAL_HOURS."""
    logger.info("Running scheduled MegaGrok poster generation…")
    ok, mob = generate_and_post(TELEGRAM_CHAT_ID, interval_hours=POST_INTERVAL_HOURS)
    if ok:
        logger.info(f"Scheduled post successful: {mob}")
    else:
        logger.error(f"Scheduled post FAILED: {mob}")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(
        scheduler_job,
        trigger="interval",
        hours=POST_INTERVAL_HOURS
    )
    
    scheduler.start()
    logger.info(f"Scheduler started. Interval: {POST_INTERVAL_HOURS} hours")

    # Run immediately once on startup
    try:
        logger.info("Running initial scheduled job…")
        scheduler_job()
    except Exception as e:
        logger.exception("Initial job failed: %s", e)

# --------------------------
# TELEGRAM COMMAND HANDLER
# --------------------------
def start_telegram():
    logger.info("Starting Telegram bot polling…")
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add all /Grokposter commands from handlers/commands.py
    for handler in get_handlers():
        dp.add_handler(handler)

    updater.start_polling()
    logger.info("Telegram bot polling started successfully")
    updater.idle()

# --------------------------
# START EVERYTHING
# --------------------------
if __name__ == "__main__":
    # Start scheduler in its own thread
    threading.Thread(target=start_scheduler, daemon=True).start()

    # Start Telegram bot in its own thread
    threading.Thread(target=start_telegram, daemon=True).start()

    # Start Flask server (Render requires an HTTP server)
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )
