import json
import os
from discord import Colour

# Load balancing data
BALANCING_FILE = os.path.join(os.path.dirname(__file__), "data", "balancing.json")

def load_balancing():
    with open(BALANCING_FILE, "r") as f:
        return json.load(f)

balancing = load_balancing()

RARITY_WEIGHTS = balancing["rarity_weights"]
GLOBAL_RESET_HOUR = balancing.get("global_reset_hour", 0)

# UI Constants (Keep in code as they are not balance-related)
RARITY_EMOJIS = {
    "Common": ":white_circle:",
    "Uncommon": ":green_circle:",
    "Rare": ":blue_circle:",
    "Epic": ":purple_circle:",
    "Legendary": ":orange_circle:",
}
RARITY_COLORS = {
    "Common": Colour.light_grey(),
    "Uncommon": Colour.green(),
    "Rare": Colour.blue(),
    "Epic": Colour.purple(),
    "Legendary": Colour.orange(),
}

TRADING_HALL_ORDER = ["farmer", "cleric", "toolsmith", "librarian"]
VALID_TOKEN_RARITIES = ["uncommon", "rare", "epic"]
