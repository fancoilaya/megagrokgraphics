# handlers/posting.py
"""
Poster generation + delivery logic for MegaGrok Graphics Bot.
Called by:
 - scheduler in main.py
 - /grokposter command (handlers/grokposter.py)

This returns raw image bytes ready for PTB20 send_photo().
"""

import io
import logging
from datetime import datetime

from services.stability_client import generate_megagrok_image

log = logging.getLogger("posting")


# ---------------------------------------------------------
# MegaGrok Style Prompt (baseline style applied to all)
# ---------------------------------------------------------

MEGAGROK_BASE_STYLE = """
MegaGrok Metaverse Poster Style:
- Neon cosmic palette (purple, green, blue)
- Sharp cinematic lighting with rim highlights
- Sci-fi crypto-fantasy aesthetic
- Clean outlines, holographic glow
- Slight grain texture like cosmic film
- Dramatic energy swirls in background
- Frog-metaverse themed visual identity
- Square or portrait poster format
"""


# ---------------------------------------------------------
# Generate Image + Prepare for Sending
# ---------------------------------------------------------

def generate_and_post(chat_id: str, interval_hours: float):
    """
    Generates a MegaGrok poster and returns:
    (True, info_string, image_bytes) on success
    (False, error_message, None) on failure
    """
    log.info(f"🎨 Generating MegaGrok poster for chat {chat_id}...")

    # You can extend this system to pick mobs, seasonal styles, etc.
    prompt = f"""
    {MEGAGROK_BASE_STYLE}

    Create a new random MegaGrok Metaverse poster.
    Must feel like part of the same universe as previous posters.
    Include cosmic energy, neon motion, and high drama.
    Poster must be visually striking and match metaverse canon.

    Timestamp: {datetime.utcnow().isoformat()}Z
    """

    try:
        # Returns raw bytes from Stability client
        img_bytes = generate_megagrok_image(prompt)

        if not img_bytes:
            log.error("No image bytes returned from generator.")
            return False, "Image generator returned no data."

        # Convert to BytesIO for Telegram
        bio = io.BytesIO(img_bytes)
        bio.name = "megagrok_poster.png"

        info = f"Poster created at {datetime.utcnow().isoformat()}Z"
        return True, info, bio

    except Exception as e:
        error_msg = f"Poster generation failed: {e}"
        log.exception(error_msg)
        return False, error_msg, None
