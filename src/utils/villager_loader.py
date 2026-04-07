import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "villagers.json"


def load_villagers() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        villagers = json.load(f)

    return villagers
