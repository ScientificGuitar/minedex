from discord import Colour

RARITY_WEIGHTS = {"Common": 55, "Uncommon": 25, "Rare": 13, "Epic": 6, "Legendary": 1}
RARITY_EMERALD_REWARDS = {
    "Common": 2,
    "Uncommon": 5,
    "Rare": 10,
    "Epic": 20,
    "Legendary": 50,
}
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

RARITY_BUCKET_TOTALS = {
    "Common": 100,
    "Uncommon": 175,
    "Rare": 300,
    "Epic": 500,
    "Legendary": 800,
}

RARITY_COMPLETION_BONUS = {
    "Common": 25,
    "Uncommon": 50,
    "Rare": 100,
    "Epic": 175,
    "Legendary": 300,
}

FULL_COLLECTION_BONUS = 500

TRADING_HALL_ORDER = ["farmer", "cleric", "toolsmith", "librarian"]

VALID_TOKEN_RARITIES = ["uncommon", "rare", "epic"]

FARMER_EMERALD_VALUES = {
    "Common": 5,
    "Uncommon": 20,
    "Rare": 50,
    "Epic": 100,
    "Legendary": 200,
}
CLERIC_RARITY_TO_TOKEN = {"Common": "uncommon", "Uncommon": "rare", "Rare": "epic"}
