# main.py — MegaGrok Graphics Bot (Webhook Mode for Render)
# ------------------------------------------------------------
# Features:
#  - Telegram webhook (PTB20 async)
#  - Flask server for webhook + health
#  - APScheduler auto-poster
#  - Stability AI image generation
#  - Modular handlers
# ------------------------------------------------------------

import os
import logging
import threading
from datetime import datetime

from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import Update
from telegram.ext import Application, ApplicationBuilder

from handlers.commands import get_handlers
from handlers.posting import generate_and_post


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", "2"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://megagrokgraphics.onrender.com

if not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")
if not CHAT_ID:
    raise RuntimeError("Missing TELEGRAM_CHAT_ID")
if not WEBHOOK_URL:
    raise RuntimeError("Missing WEBHOOK_URL")


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("megagrok-main")


# ============================================================
# FLASK APP (Webhook Receiver + Health Check)
# ============================================================

app = Flask("megagrok_graphics_bot")

@app.get("/")
def index():
    return jsonify({
        "status": "ok",
        "bot": "MegaGrok Graphics Bot",
        "time": datetime.utcnow().isoformat() + "Z"
    })


# ============================================================
# TELEGRAM PTB v20 APPLICATION
# ============================================================

app_tg: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# Register command handlers
for handler in get_handlers():
    app_tg.add_handler(handler)


# ============================================================
# TELEGRAM WEBHOOK ENDPOINT
# ============================================================

@app.post("/webhook")
def telegram_webhook():
    """Telegram sends updates here."""
    data = request.get_json(force=True)
    update = Update.de_json(data, app_tg.bot)

    # Schedule async update processing
    app_tg.create_task(app_tg.process_update(update))
    return "OK", 200


# ============================================================
# WEBHOOK REGISTRATION (async)
# ============================================================

async def set_webhook_async():
    """Register webhook URL with Telegram (async-safe)."""
    webhook = f"{WEBHOOK_URL}/webhook"
    log.info(f"🔗 Setting webhook → {webhook}")
    await app_tg.bot.set_webhook(url=webhook)


# ============================================================
# SCHEDULER (AUTO-POSTER)
# ============================================================

def scheduler_job():
    log.info("🪄 Running scheduled MegaGrok poster...")
    ok, info, img = generate_and_post(CHAT_ID, POST_INTERVAL_HOURS)

    if ok:
        # Use PTB async bot inside scheduler thread safely
        app_tg.create_task(
            app_tg.bot.send_photo(chat_id=CHAT_ID, photo=img, caption=info)
        )
        log.info(f"Posted: {info}")
    else:
        log.error(f"Failed: {info}")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(scheduler_job, "interval", hours=POST_INTERVAL_HOURS)
    scheduler.start()

    log.info(f"⏱ Scheduler started (every {POST_INTERVAL_HOURS}h)")

    # Attempt initial run
    try:
        scheduler_job()
    except Exception as e:
        log.exception(f"Initial scheduled job failed: {e}")


# ============================================================
# STARTUP SEQUENCE
# ============================================================

def start_background_services():
    log.info("🚀 MegaGrok Graphics Bot starting (WEBHOOK MODE)")

    # Start scheduler thread
    threading.Thread(target=start_scheduler, daemon=True).start()

    # Register webhook async
    app_tg.create_task(set_webhook_async())


# Initialize immediately when gunicorn imports main.py
start_background_services()


# ============================================================
# RUN FLASK SERVER (Gunicorn calls this automatically)
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
