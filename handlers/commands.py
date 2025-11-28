from telegram.ext import CommandHandler
from handlers.posting import generate_and_post

def grokposter(update, context):
    chat_id = update.effective_chat.id
    args = context.args
    mob = args[0] if args else None

    update.message.reply_text("Generating MegaGrok poster…")

    ok, info = generate_and_post(chat_id, mob_override=mob)

    if ok:
        update.message.reply_text(f"✔️ Posted {info}")
    else:
        update.message.reply_text(f"❌ Error: {info}")

def get_handlers():
    return [
        CommandHandler("Grokposter", grokposter, pass_args=True),
    ]
