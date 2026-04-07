import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "items.json"


def load_items() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    return items
