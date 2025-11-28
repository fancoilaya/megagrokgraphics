# main.py — MegaGrok Graphics Bot (Render Background Worker)
# ------------------------------------------------------------
# Features:
# - Async PTB20 Telegram bot running in separate thread
# - APScheduler auto-poster (every X hours)
# - Flask root endpoint for Render health checks
# - Modular command loading (handlers/commands.py)
# - Stability/OpenAI image generation handled by handlers/posting.py
# ------------------------------------------------------------

import os
import threading
import asyncio
import logging
from datetime import datetime

from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

# Telegram async app builder (PTB v20+)
from telegram.ext import ApplicationBuilder

# Local handlers
from handlers.commands import get_handlers
from handlers.posting import generate_and_post


# -------------------------------------------------
# Environment Variables
# -------------------------------------------------

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", "2"))

if not BOT_TOKEN:
    raise RuntimeError("❌ Missing TELEGRAM_BOT_TOKEN")

if not CHAT_ID:
    raise RuntimeError("❌ Missing TELEGRAM_CHAT_ID")


# -------------------------------------------------
# Logging
# -------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("megagrok-main")


# -------------------------------------------------
# Flask App (Render health endpoint)
# -------------------------------------------------

app = Flask("megagrok_graphics_bot")

@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "service": "MegaGrok Graphics Bot",
        "time": datetime.utcnow().isoformat() + "Z"
    })


# -------------------------------------------------
# APScheduler Auto Poster
# -------------------------------------------------

def scheduler_job():
    """Run one scheduled poster generation + Telegram post."""
    log.info("🪄 Running scheduled MegaGrok poster...")
    ok, info = generate_and_post(CHAT_ID, POST_INTERVAL_HOURS)

    if ok:
        log.info(f"✅ Posted successfully: {info}")
    else:
        log.error(f"❌ Failed: {info}")


def start_scheduler():
    """Start the repeating scheduler in a background thread."""
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(scheduler_job, "interval", hours=POST_INTERVAL_HOURS)

    sched.start()
    log.info(f"⏱ Scheduler started (every {POST_INTERVAL_HOURS} hours)")

    # Initial poster on startup
    try:
        scheduler_job()
    except Exception as e:
        log.exception(f"⚠ Initial scheduled job failed: {e}")


# -------------------------------------------------
# Telegram Async Bot Thread
# -------------------------------------------------

async def run_telegram_async():
    """Run PTB telegram polling inside asyncio."""
    log.info("🤖 Initializing Telegram bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Load commands dynamically
    for handler in get_handlers():
        app.add_handler(handler)

    log.info("📡 Starting Telegram polling...")
    await app.run_polling(drop_pending_updates=True)


def start_telegram_thread():
    """Launch Telegram polling in a dedicated thread."""
    def runner():
        asyncio.run(run_telegram_async())

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    log.info("🧵 Telegram polling thread started.")


# -------------------------------------------------
# START ALL BACKGROUND SERVICES NOW
# -------------------------------------------------

def start_background_services():
    log.info("🚀 Starting MegaGrok Graphics Bot background services...")

    # Scheduler thread
    threading.Thread(target=start_scheduler, daemon=True).start()

    # Telegram thread
    start_telegram_thread()


# IMPORTANT:
# Gunicorn imports this file exactly once on startup — so we must start services NOW.
start_background_services()


# -------------------------------------------------
# Local debug mode (not used on Render)
# -------------------------------------------------

if __name__ == "__main__":
    start_scheduler()
    start_telegram_thread()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
