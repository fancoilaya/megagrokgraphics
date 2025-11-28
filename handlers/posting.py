# handlers/posting.py
import time
import logging
from handlers.mobs import pick_mob_for_post, get_mob_by_name
from services.stability_client import generate_megagrok_image
from services.telegram_client import tg_send_photo
from style import PROMPT_TEMPLATE, MEGAGROK_STYLE

logger = logging.getLogger(__name__)

def build_prompt(mob: dict, variant: bool = False) -> str:
    mob_name = mob.get("name", "Unknown")
    mob_desc = mob.get("desc", "")
    if variant:
        mob_desc += " Slight variant: altered accent colors or a small prop."
    prompt = PROMPT_TEMPLATE.format(mob_name=mob_name, mob_desc=mob_desc, style=MEGAGROK_STYLE)
    return prompt

def generate_and_post(chat_id: str, interval_hours: float = 2, mob_override: str = None):
    """Synchronous function used by scheduler and by command handlers via asyncio.to_thread."""
    try:
        if mob_override:
            mob = get_mob_by_name(mob_override)
            if not mob:
                return False, f"Unknown mob '{mob_override}'"
            variant = False
        else:
            mob, variant = pick_mob_for_post(interval_hours)
        prompt = build_prompt(mob, variant)
        img_bytes = generate_megagrok_image(prompt)
        filename = f"{mob.get('id','mob')}_{int(time.time())}.png"
        caption = f"{mob.get('name')} — MegaGrok Poster"
        ok = tg_send_photo(chat_id, img_bytes, filename, caption)
        return ok, mob.get("name")
    except Exception as e:
        logger.exception("generate_and_post failed: %s", e)
        return False, str(e)
