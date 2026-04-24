import random
from typing import Any, Dict, List, Optional, Tuple

from constants import RARITY_WEIGHTS
from database.collection import Collection as CollectionDB
from database.inventory import Inventory as InventoryDB
from database.user import User as UserDB, is_same_game_day


class EconomyService:
    def __init__(self, mobs: Dict[str, Dict], mobs_by_rarity: Dict[str, List[str]], items: Dict[str, Dict]):
        self.mobs = mobs
        self.mobs_by_rarity = mobs_by_rarity
        self.items = items

    def get_user_balance(self, session_factory, guild_id: int, user_id: int) -> int:
        """Get user's emerald balance."""
        return UserDB.get_emeralds(session_factory, guild_id, user_id)

    def get_user_inventory(self, session_factory, guild_id: int, user_id: int) -> Dict[str, List[Tuple[Dict, int]]]:
        """Get user's inventory grouped by item type."""
        inventory = InventoryDB.get_items(session_factory, guild_id, user_id)
        grouped = {}

        for item in inventory or []:
            item_id = item.item_id
            amount = item.amount

            if amount <= 0:
                continue

            item_data = self.items.get(item_id)
            if not item_data:
                continue

            item_type = item_data.get("type", "misc")
            grouped.setdefault(item_type, []).append((item_data, amount))

        return grouped

    def get_item_info(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific item."""
        return self.items.get(item_id)

    def claim_daily_reward(self, session_factory, guild_id: int, user_id: int, now: int) -> Dict[str, Any]:
        """Claim daily reward if available."""
        user = UserDB.get_user(session_factory, guild_id, user_id)
        last_daily_claim_at = user.last_daily_at if user else None

        if is_same_game_day(last_daily_claim_at, now):
            return {"error": "You've already claimed today."}

        emeralds = random.randint(2, 5)
        mob_id, mob = self.roll_random_mob(allowed={"Common"})

        UserDB.update_last_daily_at(session_factory, guild_id, user_id, now)
        UserDB.add_emeralds(session_factory, guild_id, user_id, emeralds)
        CollectionDB.add_to_collection(session_factory, guild_id, user_id, mob_id)

        return {"emeralds": emeralds, "mob": mob}

    def roll_random_mob(self, exclude: Optional[set] = None, allowed: Optional[set] = None) -> Tuple[str, Dict]:
        """Roll a random mob based on rarity weights."""
        rarity = self.roll_rarity(exclude, allowed)
        mob_id = random.choice(self.mobs_by_rarity[rarity])
        return mob_id, self.mobs[mob_id]

    @staticmethod
    def roll_rarity(exclude: Optional[set] = None, allowed: Optional[set] = None) -> str:
        """Roll a rarity based on weights."""
        exclude = exclude or set()
        if allowed:
            rarities = [r for r in allowed if r in RARITY_WEIGHTS]
        else:
            rarities = [r for r in RARITY_WEIGHTS if r not in exclude]
        weights = [RARITY_WEIGHTS[r] for r in rarities]

        return random.choices(rarities, weights=weights, k=1)[0]
