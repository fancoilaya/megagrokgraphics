from handlers.mobs import pick_mob_for_post, get_mob_by_name
from services.openai_client import generate_megagrok_image
from services.telegram_client import tg_send_photo
from style import PROMPT_TEMPLATE, MEGAGROK_STYLE
import time

def build_prompt(mob, variant=False):
    desc = mob["desc"]
    if variant:
        desc += " (variant accent colors)"
    return PROMPT_TEMPLATE.format(
        mob_name=mob["name"],
        mob_desc=desc,
        style=MEGAGROK_STYLE
    )

def generate_and_post(chat_id, interval_hours=2, mob_override=None):
    if mob_override:
        mob = get_mob_by_name(mob_override)
        if not mob:
            return False, f"Unknown mob '{mob_override}'"
        variant = False
    else:
        mob, variant = pick_mob_for_post(interval_hours)

    prompt = build_prompt(mob, variant)
    img = generate_megagrok_image(prompt)

    filename = f"{mob['id']}_{int(time.time())}.png"
    caption = f"{mob['name']} — MegaGrok Poster"

    ok = tg_send_photo(chat_id, img, filename, caption)
    return ok, mob["name"]
