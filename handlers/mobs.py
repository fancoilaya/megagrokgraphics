import os
import json
import random
import time

# Default mob list
MOBS = [
    {"id": "rugrat", "name": "RugRat", "desc": "tiny rodent-like liquidity gremlin holding a miniature rug"},
    {"id": "hopslime", "name": "Hop Slime", "desc": "goo-based frog-slime with translucent green body"},
    {"id": "fudling", "name": "FUDling", "desc": "small furry creature with glowing purple eyes"},
    {"id": "hopgoblin", "name": "HopGoblin", "desc": "mischievous goblin with a spiked club"},
    {"id": "croakling", "name": "Croakling", "desc": "aggressive frog-like warrior"},
    # add all 25 here...
]

# Optional JSON override
MOBS_JSON_PATH = os.getenv("MOBS_JSON_PATH")
if MOBS_JSON_PATH and os.path.exists(MOBS_JSON_PATH):
    try:
        with open(MOBS_JSON_PATH, "r") as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                MOBS = data
    except Exception:
        pass

def pick_mob_for_post(interval_hours=2):
    """Rotation with randomness."""
    idx = int((time.time() // (interval_hours * 3600)) % len(MOBS))
    idx = (idx + random.randint(0, len(MOBS)-1)) % len(MOBS)
    mob = MOBS[idx]
    variant = random.random() < 0.3
    return mob, variant

def get_mob_by_name(name):
    name = name.lower()
    for m in MOBS:
        if m["id"].lower() == name or m["name"].lower() == name:
            return m
    return None
