# services/stability_client.py

import os
import base64
import requests

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
if not STABILITY_API_KEY:
    raise RuntimeError("Missing STABILITY_API_KEY")

API_URL = os.getenv(
    "STABILITY_API_URL",
    # Ultra model default endpoint
    "https://api.stability.ai/v2beta/stable-image/generate/ultra"
)

HEADERS = {
    "Authorization": f"Bearer {STABILITY_API_KEY}",
    # MUST request an image type:
    "Accept": "image/png",
    # DO NOT set Content-Type manually (requests handles multipart properly)
}

def generate_megagrok_image(prompt: str) -> bytes:
    """
    Stability Ultra — return raw PNG bytes.
    """

    # Required form fields
    data = {
        "prompt": prompt,
        "aspect_ratio": "1:1",
        "output_format": "png",
    }

    # Ultra requires at least one valid "files" part for multipart,
    # but you can send an empty placeholder.
    files = {
        "none": ("", b"", "application/octet-stream")
    }

    resp = requests.post(
        API_URL,
        headers=HEADERS,
        data=data,
        files=files,
        timeout=120
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Stability API error {resp.status_code}: {resp.text}"
        )

    # Ultra endpoint returns raw PNG bytes directly (NOT JSON!)
    return resp.content
