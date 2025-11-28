# services/openai_client.py
import os
import base64
import time
import openai
import logging

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1024x1024")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

def generate_megagrok_image(prompt: str) -> bytes:
    """Synchronous call to OpenAI Images API. Returns raw bytes."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("OpenAI image generation attempt %d", attempt)
            resp = openai.Image.create(
                prompt=prompt,
                n=1,
                size=IMAGE_SIZE
            )
            # handle dict or object
            b64 = None
            if isinstance(resp, dict):
                b64 = resp["data"][0].get("b64_json")
            else:
                try:
                    b64 = resp.data[0].b64_json
                except Exception:
                    b64 = None
            if not b64:
                raise RuntimeError("OpenAI returned no image data")
            return base64.b64decode(b64)
        except Exception as e:
            logger.exception("OpenAI image generation failed on attempt %d: %s", attempt, e)
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
            else:
                raise
