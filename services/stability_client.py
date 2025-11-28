# services/stability_client.py
"""
Stability AI Image Generator for MegaGrok Metaverse Posters.
Returns raw PNG bytes ready for BytesIO.
"""

import os
import base64
import requests

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

if not STABILITY_API_KEY:
    raise RuntimeError("❌ Missing STABILITY_API_KEY environment variable")


# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

STABILITY_URL = "https://api.stability.ai/v2beta/stable-image/generate/ultra"

HEADERS = {
    "Authorization": f"Bearer {STABILITY_API_KEY}",
    "Accept": "application/json"
}


def generate_megagrok_image(prompt: str) -> bytes:
    """
    Sends prompt to Stability Ultra and returns raw PNG bytes.
    """

    data = {
        "prompt": prompt,
        "output_format": "png",
        "aspect_ratio": "1:1",           # good for posters
        "model": "stable-image-ultra",   # ultra-quality model
    }

    response = requests.post(
        STABILITY_URL,
        headers=HEADERS,
        files={"none": ""},
        data=data,
        timeout=120,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Stability API Error {response.status_code}: {response.text}"
        )

    payload = response.json()

    if "image" not in payload:
        raise RuntimeError("Stability API returned no image data")

    # The image is base64-encoded PNG → decode to raw bytes
    return base64.b64decode(payload["image"])
