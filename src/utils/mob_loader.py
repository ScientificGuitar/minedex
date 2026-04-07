import json
from collections import defaultdict
from pathlib import Path

RARITIES = {"Common", "Uncommon", "Rare", "Epic", "Legendary"}
REQUIRED_FIELDS = {"name", "rarity", "image", "lore"}
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "mobs.json"


def load_mobs() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        mobs = json.load(f)

    return mobs


def validate_mobs(mobs: dict) -> None:
    for mob_id, mob in mobs.items():
        missing = REQUIRED_FIELDS - mob.keys()
        if missing:
            raise ValueError(f"Mob '{mob_id}' is missing fields: {', '.join(missing)}")

        if mob["rarity"] not in RARITIES:
            raise ValueError(f"Mob '{mob_id}' has invalid rarity '{mob['rarity']}'")


def group_mobs_by_rarity(mobs: dict) -> dict[str, list[str]]:
    mobs_by_rarity = defaultdict(list)

    for mob_id, mob in mobs.items():
        mobs_by_rarity[mob["rarity"]].append(mob_id)

    return dict(mobs_by_rarity)


def load_mob_data():
    mobs = load_mobs()
    validate_mobs(mobs)
    mobs_by_rarity = group_mobs_by_rarity(mobs)
    return mobs, mobs_by_rarity
