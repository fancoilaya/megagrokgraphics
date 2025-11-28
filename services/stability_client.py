# services/stability_client.py

import os
import base64
import requests

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

if not STABILITY_API_KEY:
    raise RuntimeError("Missing STABILITY_API_KEY")


API_URL = "https://api.stability.ai/v2beta/stable-image/generate/ultra"

HEADERS = {
    "Authorization": f"Bearer {STABILITY_API_KEY}",
}


def generate_megagrok_image(prompt: str) -> bytes:
    """
    Correct Stability request:
    - multipart/form-data
    - 'prompt' must be in data fields
    - NO bogus file field
    """

    data = {
        "prompt": prompt,
        "output_format": "png",
        "aspect_ratio": "1:1",
    }

    # Proper multipart request WITHOUT a dummy file
    response = requests.post(
        API_URL,
        headers=HEADERS,
        data=data,
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Stability API error {response.status_code}: {response.text}"
        )

    j = response.json()

    if "image" not in j:
        raise RuntimeError("Stability API returned no image data")

    return base64.b64decode(j["image"])
