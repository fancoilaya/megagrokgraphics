# handlers/grokposter.py
import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from handlers.posting import generate_and_post

logger = logging.getLogger("grokposter")


async def grokposter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User command: /grokposter [optional_mob_name]"""
    chat_id = update.effective_chat.id

    # Extract mob name override, if provided
    mob_override = None
    if context.args:
        mob_override = " ".join(context.args).strip()

    await context.bot.send_message(
        chat_id,
        "⚙️ MegaForge Prime Engine: generating your MegaGrok poster..."
    )

    # Call your existing function (sync), but inside executor
    try:
        ok, info = await context.application.run_in_executor(
            None,
            lambda: generate_and_post(chat_id, interval_hours=None, mob_override=mob_override)
        )

        if not ok:
            await context.bot.send_message(
                chat_id,
                f"❌ Poster generation failed: {info}"
            )
    except Exception as e:
        logger.exception("Unhandled error in /grokposter: %s", e)
        await context.bot.send_message(chat_id, f"❌ Unexpected error: {e}")


def get_handler():
    """Returned in handlers.commands.get_handlers()"""
    return CommandHandler("grokposter", grokposter)
