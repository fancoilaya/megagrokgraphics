# services/stability_client.py

import os
import base64
import requests

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

if not STABILITY_API_KEY:
    raise RuntimeError("Missing STABILITY_API_KEY")

API_URL = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

HEADERS = {
    "Authorization": f"Bearer {STABILITY_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

def generate_megagrok_image(prompt: str) -> bytes:
    """
    Generates a 1:1 poster-style image using Stability AI SD3.
    Returns raw PNG bytes.
    """

    payload = {
        "prompt": prompt,
        "aspect_ratio": "1:1",
        "output_format": "png"
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"Stability API error {response.status_code}: {response.text}"
        )

    data = response.json()
    b64_image = data["image"]

    return base64.b64decode(b64_image)
