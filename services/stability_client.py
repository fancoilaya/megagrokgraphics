# services/stability_client.py

import os
import base64
import logging
import requests

log = logging.getLogger(__name__)

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
if not STABILITY_API_KEY:
    raise RuntimeError("STABILITY_API_KEY not set")

STABILITY_URL = "https://api.stability.ai/v2beta/stable-image/generate/sd3"


def generate_megagrok_image(prompt: str) -> bytes:
    """
    Calls Stability SD3 API properly.
    Returns raw PNG bytes.
    """

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "output_format": "png",   # stability returns base64 png
        "mode": "text-to-image",
        "aspect_ratio": "1:1"
    }

    resp = requests.post(STABILITY_URL, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Stability API error {resp.status_code}: {resp.text}"
        )

    try:
        data = resp.json()
        b64_img = data["image"]  # stability returns: {"image": "<base64>"}
        return base64.b64decode(b64_img)

    except Exception as e:
        log.exception("Failed decoding Stability response")
        raise RuntimeError(f"Invalid Stability response: {resp.text}")
