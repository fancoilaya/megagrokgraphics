# handlers/commands.py
import asyncio
import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from handlers.posting import generate_and_post

logger = logging.getLogger(__name__)

async def grokposter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    mob_override = args[0] if args else None

    await update.message.reply_text("Generating MegaGrok poster... this may take a few seconds.")

    # run blocking generation in a thread
    ok, info = await asyncio.to_thread(generate_and_post, chat_id, None, mob_override)

    if ok:
        await update.message.reply_text(f"Done — Posted: {info}")
    else:
        await update.message.reply_text(f"Error generating poster: {info}")

def get_handlers():
    return [
        CommandHandler("Grokposter", grokposter)
    ]
