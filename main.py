# main.py — MegaGrok Graphics Bot (Webhook Mode — Event Loop Safe)
# ------------------------------------------------------------
# Fixes:
#  - "no running event loop"
#  - "coroutine was never awaited"
#  - PTB20 async startup before loop exists
#  - webhook registration timing
#  - Gunicorn cannot find app (now app = flask_app)
# ------------------------------------------------------------

import os
import logging
import asyncio
import threading
from datetime import datetime

from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import Update
from telegram.ext import ApplicationBuilder

from handlers.commands import get_handlers
from handlers.posting import generate_and_post


# ============================================================
# ENVIRONMENT
# ============================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://megagrokgraphics.onrender.com
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", "2"))

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
# GLOBAL EVENT LOOP (Dedicated Telegram Loop)
# ============================================================

bot_loop = asyncio.new_event_loop()


async def build_application():
    """Build PTB20 Application inside event loop."""
    app_tg = ApplicationBuilder().token(BOT_TOKEN).build()

    # Load commands
    for h in get_handlers():
        app_tg.add_handler(h)

    return app_tg


# Build the PTB bot inside the event loop
app_tg = bot_loop.run_until_complete(build_application())


# ============================================================
# TELEGRAM LOOP THREAD
# ============================================================

def telegram_loop_thread():
    """Runs Telegram bot forever in its own event loop."""
    asyncio.set_event_loop(bot_loop)
    log.info("📡 Telegram event loop started.")

    async def _init_webhook():
        real_url = f"{WEBHOOK_URL}/webhook"
        log.info(f"🔗 Setting webhook: {real_url}")
        await app_tg.bot.set_webhook(url=real_url)

    bot_loop.create_task(_init_webhook())
    bot_loop.run_forever()


threading.Thread(target=telegram_loop_thread, daemon=True).start()


# ============================================================
# FLASK APP
# ============================================================

flask_app = Flask("megagrok_graphics_bot")

# Expose Flask app to Gunicorn as "app"
app = flask_app


@flask_app.get("/")
def index():
    return jsonify({
        "status": "ok",
        "bot": "MegaGrok Graphics Bot",
        "time": datetime.utcnow().isoformat() + "Z"
    })


@flask_app.post("/webhook")
def telegram_webhook():
    """Receive Telegram update and dispatch to PTB event loop."""
    data = request.get_json(force=True)
    update = Update.de_json(data, app_tg.bot)

    bot_loop.call_soon_threadsafe(
        lambda: bot_loop.create_task(app_tg.process_update(update))
    )

    return "OK", 200


# ============================================================
# SCHEDULER (Auto-poster)
# ============================================================

def scheduler_job():
    log.info("🪄 Running scheduled MegaGrok poster...")
    ok, info, img = generate_and_post(CHAT_ID, POST_INTERVAL_HOURS)

    if ok:
        # Inject Telegram send into async bot loop
        bot_loop.call_soon_threadsafe(
            lambda: bot_loop.create_task(
                app_tg.bot.send_photo(chat_id=CHAT_ID, photo=img, caption=info)
            )
        )
        log.info(f"Posted: {info}")
    else:
        log.error(f"Auto-poster failed: {info}")


def start_scheduler():
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(scheduler_job, "interval", hours=POST_INTERVAL_HOURS)
    sched.start()

    log.info(f"⏱ Scheduler started (every {POST_INTERVAL_HOURS} hours)")

    # Run once at startup
    try:
        scheduler_job()
    except Exception as e:
        log.exception(f"Initial scheduled job failed: {e}")


threading.Thread(target=start_scheduler, daemon=True).start()


# ============================================================
# ENTRYPOINT (Gunicorn loads `app`)
# ============================================================

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
