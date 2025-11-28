# handlers/posting.py
import time
import io
import logging

logger = logging.getLogger("posting")

# Try stability first
try:
    from services.stability_client import generate_megagrok_image
    BACKEND = "stability"
except Exception:
    BACKEND = None
    generate_megagrok_image = None


# Try mobs module
try:
    from handlers.mobs import pick_mob_for_post, get_mob_by_name
except Exception:
    def pick_mob_for_post(_):
        return {
            "id": "rugrat",
            "name": "RugRat",
            "desc": "tiny rodent-like liquidity gremlin with neon red accents, glowing eyes and cosmic glitch effects"
        }, False

    def get_mob_by_name(name: str):
        return None


# Try user style module
try:
    from style import PROMPT_TEMPLATE, MEGAGROK_STYLE
except Exception:
    MEGAGROK_STYLE = (
        "MegaGrok Poster Style — neon cosmic palette, vibrant blues, purples, greens, "
        "sharp cinematic highlights, holographic glow, dramatic rim lighting, heavy contrast, "
        "clean outlines, slight grain texture, sci-fi crypto aesthetic, frog-metaverse themes."
    )

    PROMPT_TEMPLATE = (
        "Poster of the creature.\n"
        "Name: {mob_name}\n"
        "Description: {mob_desc}\n\n"
        "Style:\n{style}\n\n"
        "Layout:\n"
        "- MEGAGROK title at top\n"
        "- Creature centered\n"
        "- Name in framed bottom box\n"
        "Vintage printed arcade poster style, bold outlines, dramatic composition."
    )


def build_prompt(mob: dict, variant: bool) -> str:
    desc = mob["desc"]
    if variant:
        desc += " Variant version with alternate accent colors."

    return PROMPT_TEMPLATE.format(
        mob_name=mob["name"],
        mob_desc=desc,
        style=MEGAGROK_STYLE
    )


def generate_and_post(chat_id: str, interval_hours=None, mob_override: str = None):
    """Sync function called inside an executor by Telegram & scheduler."""
    if BACKEND is None:
        return False, "No backend found (set STABILITY_API_KEY)"

    try:
        # Select mob (override or auto)
        if mob_override:
            mob = get_mob_by_name(mob_override)
            if not mob:
                mob = {"id": mob_override, "name": mob_override, "desc": mob_override}
            variant = False
        else:
            mob, variant = pick_mob_for_post(interval_hours or 2)

        prompt = build_prompt(mob, variant)

        # Generate image from Stability
        img_bytes = generate_megagrok_image(prompt)

        from main import_TELEGRAM_SEND_FN  # injected by main.py
        caption = f"{mob['name']} — MegaGrok Poster"

        _TELEGRAM_SEND_FN(chat_id, img_bytes, caption)
        return True, mob["name"]

    except Exception as e:
        logger.exception("Poster generation error: %s", e)
        return False, str(e)
