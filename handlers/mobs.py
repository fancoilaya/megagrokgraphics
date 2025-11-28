# handlers/mobs.py
import os
import json
import random
import time

MOBS = [
    {"id": "rugrat", "name": "RugRat", "desc": "tiny rodent-like liquidity gremlin holding a miniature rug, neon red accents, glowing eyes, cosmic glitch effects"},
    {"id": "hopslime", "name": "Hop Slime", "desc": "goo-based frog-slime with translucent green body and floating bubbles"},
    {"id": "fudling", "name": "FUDling", "desc": "small furry creature with glowing purple eyes and faint shadow aura"},
    {"id": "hopgoblin", "name": "HopGoblin", "desc": "small goblin with spiked club and mischievous grin"},
    {"id": "croakling", "name": "Croakling", "desc": "frog-like fighter with a fierce expression and muscular cartoon proportions"},
    # add up to 25 mobs...
]

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
    if random.random() < 0.3:
        mob = random.choice(MOBS)
        variant = True
    else:
        idx = int((time.time() // (interval_hours * 3600)) % len(MOBS))
        idx = (idx + random.randint(0, len(MOBS)-1)) % len(MOBS)
        mob = MOBS[idx]
        variant = False
    return mob, variant

def get_mob_by_name(name):
    if not name:
        return None
    name = name.lower()
    for m in MOBS:
        if m["id"].lower() == name or m["name"].lower() == name:
            return m
    return None
