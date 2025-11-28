# handlers/grokposter.py
"""
Async PTB20 command handler for /grokposter
Generates a MegaGrok poster on demand using Stability AI.
"""

from telegram.ext import CommandHandler, ContextTypes
from telegram import Update

from handlers.posting import generate_and_post


async def grokposter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await update.message.reply_text("⚡ MegaForge Prime Engine is generating your MegaGrok poster...")

    ok, info, img_bytes = generate_and_post(chat_id, 0)

    if ok:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=img_bytes,
            caption=f"✅ Poster generated!\n{info}"
        )
    else:
        await update.message.reply_text(f"❌ Poster generation failed:\n{info}")


def get_handler():
    """Required by handlers/commands.py to register this module."""
    return CommandHandler("grokposter", grokposter_cmd)
