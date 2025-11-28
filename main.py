import os
import io
import time
import json
import logging
import random
import base64
import requests
from datetime import datetime
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from requests import RequestException

# optionally import dotenv for local testing
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import openai

# --------------------------
# Configuration (env vars)
# --------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # group id (negative for supergroups)
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", "2"))  # default 2 hours
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1024x1024")  # or "512x512"
IMAGE_FORMAT = os.getenv("IMAGE_FORMAT", "png")  # png or webp/jpg
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

if not (OPENAI_API_KEY and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
    raise RuntimeError("Missing required env vars. Please set OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")

openai.api_key = OPENAI_API_KEY

# --------------------------
# Logging
# --------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("megagrok-graphics-bot")

# --------------------------
# Flask app (health endpoint)
# --------------------------
app = Flask("megagrok_graphics_bot")

@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "service": "megagrok_graphics_bot",
        "time": datetime.utcnow().isoformat() + "Z"
    })

# --------------------------
# Mob list (one source of truth)
# You can expand this list with up to 25 mobs.
# Each mob is a dict with name and short descriptor used to customize the prompt.
# --------------------------
MOBS = [
    {"id": "rugrat", "name": "RugRat", "desc": "tiny rodent-like liquidity gremlin holding a miniature rug, neon red accents, glowing eyes, cosmic glitch effects"},
    {"id": "hopslime", "name": "Hop Slime", "desc": "goo-based frog-slime with translucent green body and floating bubbles"},
    {"id": "fudling", "name": "FUDling", "desc": "small furry creature with glowing purple eyes and faint shadow aura"},
    {"id": "hopgoblin", "name": "HopGoblin", "desc": "small goblin with spiked club and mischievous grin"},
    {"id": "croakling", "name": "Croakling", "desc": "frog-like fighter with a fierce expression and muscular cartoon proportions"},
    # Add up to 25 mobs...
]

# If you want to use external file: check env MOBS_JSON_PATH
MOBS_JSON_PATH = os.getenv("MOBS_JSON_PATH")
if MOBS_JSON_PATH and os.path.exists(MOBS_JSON_PATH):
    try:
        with open(MOBS_JSON_PATH, "r") as f:
            loaded = json.load(f)
            if isinstance(loaded, list) and loaded:
                MOBS = loaded
                logger.info("Loaded MOBS from %s", MOBS_JSON_PATH)
    except Exception as e:
        logger.warning("Failed to load mobs from %s: %s", MOBS_JSON_PATH, e)

# --------------------------
# Locked MegaGrok Style guide (will be appended to every prompt)
# Keep this stable for consistent generations.
# --------------------------
MEGAGROK_STYLE = (
    "MegaGrok Poster Style — neon cosmic palette, vibrant blues, purples, greens, "
    "sharp cinematic highlights, slight holographic glow, dramatic rim lighting, heavy contrast, "
    "clean outlines, slight grain texture, sci-fi crypto aesthetic, frog-metaverse themes, dynamic pose. "
    "Retro arcade poster composition with MEGAGROK title at top and mob name in a framed box at bottom. "
    "High-contrast cell-shading, vintage print texture. No hyper-real neon glare; retain printed poster vibe."
)

# Prompt template
PROMPT_TEMPLATE = (
    "Create a single, portrait poster (square 1:1 or 3:4) of the creature:\n"
    "Name: {mob_name}\n"
    "Description: {mob_desc}\n\n"
    "Style instructions:\n"
    "{style}\n\n"
    "Layout:\n"
    "- MEGAGROK title at the top (bold arcade/block text)\n"
    "- Creature centered in the middle\n"
    "- Creature name in a framed box at the bottom (readable)\n\n"
    "Visual target: vintage arcade cabinet poster / printed game ad from 1990s-2000s. "
    "Use warm but neon-tinged palette (deep oranges, muted blues with neon accents), slightly grainy screen-print texture, heavy inked outlines, thick borders, bold shapes. "
    "Dramatic hard-edged shadows and stylized highlights. Include small HUD-like vintage UI elements (optional). "
    "Render as a poster-style illustration, not photorealistic. "
    "Return an energetic, cohesive poster that fits the MegaGrok universe."
)

# --------------------------
# Helpers
# --------------------------
def pick_mob_for_post(counter=None):
    """Simple rotation with a bit of randomness / variants.
       If you want strict rotation, store last index externally (e.g., Redis / file)."""
    # Weighted behavior: 70% pick next in list by rotating with randomness,
    # 30% generate a variant around a random mob.
    if random.random() < 0.3:
        mob = random.choice(MOBS)
        variant = True
    else:
        # pseudo-rotation based on time
        idx = int((time.time() // (POST_INTERVAL_HOURS * 3600)) % max(1, len(MOBS)))
        # add small jitter
        idx = (idx + random.randint(0, len(MOBS)-1)) % len(MOBS)
        mob = MOBS[idx]
        variant = False
    return mob, variant

def build_prompt(mob, variant=False):
    mob_name = mob.get("name", "Unknown")
    mob_desc = mob.get("desc", "")
    extra_variant_text = ""
    if variant:
        extra_variant_text = "Create a subtle variant: slightly different color accents or a minor prop change (e.g., glowing eyes color swap, small accessory)."
    prompt = PROMPT_TEMPLATE.format(mob_name=mob_name, mob_desc=mob_desc + (" " + extra_variant_text if extra_variant_text else ""), style=MEGAGROK_STYLE)
    return prompt

def generate_image_from_openai(prompt, size=IMAGE_SIZE, retries=MAX_RETRIES):
    """Call OpenAI Images API and return bytes."""
    for attempt in range(1, retries+1):
        try:
            logger.info("Generating image (attempt %d)...", attempt)
            # The openai.Images.create endpoint returns b64 in data[0].b64_json for many SDK versions.
            # Using the Python SDK wrapper:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size=size
            )
            # response.data[0].b64_json is typical
            b64 = None
            if isinstance(response, dict):
                # Some wrappers return raw dict
                b64 = response["data"][0].get("b64_json")
            else:
                # openai library objects often expose .data
                try:
                    b64 = response.data[0].b64_json
                except Exception:
                    b64 = None
            if not b64:
                logger.error("No base64 image returned by OpenAI on attempt %d", attempt)
                raise RuntimeError("OpenAI returned no image data")
            img_bytes = base64.b64decode(b64)
            return img_bytes
        except Exception as e:
            logger.exception("OpenAI image generation failed on attempt %d: %s", attempt, e)
            time.sleep(2 ** attempt)
    raise RuntimeError("Failed to generate image after retries")

def send_photo_to_telegram(image_bytes, filename, caption=None):
    """Send image_bytes to Telegram chat via sendPhoto (multipart)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {
        "photo": (filename, io.BytesIO(image_bytes), f"image/{IMAGE_FORMAT}")
    }
    data = {"chat_id": TELEGRAM_CHAT_ID}
    if caption:
        data["caption"] = caption
    try:
        resp = requests.post(url, data=data, files=files, timeout=30)
        resp.raise_for_status()
        j = resp.json()
        if not j.get("ok"):
            logger.error("Telegram API rejected photo: %s", j)
            raise RequestException("Telegram rejected upload")
        logger.info("Photo posted to Telegram chat %s", TELEGRAM_CHAT_ID)
        return True
    except RequestException as e:
        logger.exception("Failed to send photo to Telegram: %s", e)
        return False

# --------------------------
# Main job
# --------------------------
def job_generate_and_post():
    start_ts = time.time()
    try:
        mob, variant = pick_mob_for_post()
        prompt = build_prompt(mob, variant)
        logger.info("Selected mob: %s (variant=%s)", mob.get("name"), variant)
        logger.debug("Prompt:\n%s", prompt)

        # Generate
        img_bytes = generate_image_from_openai(prompt)

        # Prepare filename and caption
        filename = f"{mob.get('id','mob')}_{int(time.time())}.png"
        caption = f"{mob.get('name')} — MegaGrok Poster\nStyle: MegaGrok Poster Style"
        # Send
        ok = send_photo_to_telegram(img_bytes, filename, caption=caption)
        if not ok:
            logger.error("Failed to post image for mob %s", mob.get("name"))
        else:
            elapsed = time.time() - start_ts
            logger.info("Completed job for %s in %.1f sec", mob.get("name"), elapsed)
    except Exception as e:
        logger.exception("Error in scheduled job: %s", e)

# --------------------------
# Scheduler setup
# --------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(job_generate_and_post, 'interval', hours=POST_INTERVAL_HOURS, next_run_time=datetime.utcnow())
scheduler.start()
logger.info("Scheduler started: posting every %s hours", POST_INTERVAL_HOURS)

# Run first job at startup (non-blocking)
try:
    logger.info("Running initial post job at startup...")
    job_generate_and_post()
except Exception as e:
    logger.exception("Initial job failed: %s", e)

# --------------------------
# Run Flask (Render expects an HTTP server)
# --------------------------
if __name__ == "__main__":
    # Use built-in Flask server for local testing; in production use gunicorn
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
