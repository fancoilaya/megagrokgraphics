# services/openai_client.py

import base64
import os
from openai import OpenAI

client = OpenAI()

IMAGE_SIZE = "1024x1024"


def generate_megagrok_image(prompt: str) -> bytes:
    """
    Generates a MegaGrok poster image using the new OpenAI Images API (v1+).
    Returns raw PNG bytes.
    """

    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=IMAGE_SIZE,
        n=1,
    )

    # Extract base64 image data
    b64_data = response.data[0].b64_json
    return base64.b64decode(b64_data)

