# main.py — MegaGrok Graphics Bot (Webhook Mode for Render)
# ------------------------------------------------------------
# Features:
# - Telegram webhook (PTB20) served through Flask
# - APScheduler for auto-poster
# - Stability image generation (services/stability_client.py)
# - Modular command handlers
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


# -------------------------------------------------
# Env Vars
# -------------------------------------------------

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", "2"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://yourapp.onrender.com/webhook

if not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")
if not CHAT_ID:
    raise RuntimeError("Missing TELEGRAM_CHAT_ID")
if not WEBHOOK_URL:
    raise RuntimeError("Missing WEBHOOK_URL")


# -------------------------------------------------
# Logging
# -------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("megagrok-main")


# -------------------------------------------------
# Flask App (webhook receiver + health endpoint)
# -------------------------------------------------

app = Flask("megagrok_graphics_bot")

@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "bot": "MegaGrok Graphics Bot",
        "time": datetime.utcnow().isoformat() + "Z"
    })


# -------------------------------------------------
# Telegram Bot Application (PTB20)
# -------------------------------------------------

# Create PTB Application once
app_tg: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# Register handlers
for h in get_handlers():
    app_tg.add_handler(h)


# -------------------------------------------------
# Webhook endpoint
# -------------------------------------------------

@app.post("/webhook")
def webhook():
    """Receives Telegram updates via webhook."""
    data = request.get_json(force=True)
    update = Update.de_json(data, app_tg.bot)
    app_tg.create_task(app_tg.process_update(update))
    return "OK", 200


# -------------------------------------------------
# Scheduler (Auto Poster)
# -------------------------------------------------

def scheduler_job():
    log.info("🪄 Running scheduled MegaGrok poster...")
    ok, info, img = generate_and_post(CHAT_ID, POST_INTERVAL_HOURS)

    if ok:
        # Using the PTB async method inside sync scheduler: use create_task
        app_tg.create_task(
            app_tg.bot.send_photo(chat_id=CHAT_ID, photo=img, caption=info)
        )
        log.info(f"Posted: {info}")
    else:
        log.error(f"Failed: {info}")


def start_scheduler():
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(scheduler_job, "interval", hours=POST_INTERVAL_HOURS)
    sched.start()
    log.info(f"⏱ Scheduler started (every {POST_INTERVAL_HOURS} hours)")

    # Initial post on startup
    try:
        scheduler_job()
    except Exception as e:
        log.exception(f"Initial scheduled job failed: {e}")


# -------------------------------------------------
# Startup sequence
# -------------------------------------------------

def on_startup():
    log.info("🚀 MegaGrok Graphics Bot starting (WEBHOOK MODE)")

    # Start Scheduler in background thread
    threading.Thread(target=start_scheduler, daemon=True).start()

    # Set webhook
    log.info(f"🔗 Setting webhook → {WEBHOOK_URL}/webhook")
    app_tg.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

on_startup()


# -------------------------------------------------
# Flask server run (Render handles Gunicorn)
# -------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
