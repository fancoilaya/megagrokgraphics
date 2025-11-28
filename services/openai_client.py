import os
import base64
import openai
import time

openai.api_key = os.getenv("OPENAI_API_KEY")
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1024x1024")

def generate_megagrok_image(prompt):
    retries = 3
    for attempt in range(retries):
        try:
            resp = openai.Image.create(
                prompt=prompt,
                n=1,
                size=IMAGE_SIZE
            )
            b64 = resp["data"][0]["b64_json"]
            return base64.b64decode(b64)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)

