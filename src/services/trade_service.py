from typing import Dict

from constants import CLERIC_RARITY_TO_TOKEN, FARMER_EMERALD_VALUES
from database.collection import Collection as CollectionDB
from database.inventory import Inventory as InventoryDB
from database.user import User as UserDB


class TradeService:
    def __init__(self, mobs: Dict[str, Dict], villagers: Dict[str, Dict], items: Dict[str, Dict]):
        self.mobs = mobs
        self.villagers = villagers
        self.items = items

    def can_trade_with_farmer(self, session_factory, guild_id: int, user_id: int, mob_id: str, mob_amount: int) -> Dict:
        """Check if user can trade with farmer."""
        user = UserDB.get_user(session_factory, guild_id, user_id)
        user_trading_hall_level = user.trading_hall_level if user else 0

        if user_trading_hall_level < self.villagers["farmer"]["level"]:
            return {
                "can_trade": False,
                "error": "Your village doesn't have a Farmer yet! Upgrade your Trading Hall to trade your duplicate mobs for emeralds!",
            }

        mob = self.mobs.get(mob_id)
        if not mob:
            return {"can_trade": False, "error": "That mob does not exist."}

        user_mob_count = CollectionDB.get_mob_count(session_factory, guild_id, user_id, mob_id) or 0
        if user_mob_count <= 1:
            return {
                "can_trade": False,
                "error": "You don't have any **duplicate copies** of this mob to trade.\n_The Farmer only buys duplicates._",
            }

        if mob_amount >= user_mob_count:
            return {
                "can_trade": False,
                "error": f"You must keep **at least 1 copy** of each mob.\nYou can trade **up to {user_mob_count - 1}** of this mob.",
            }

        return {"can_trade": True, "mob": mob}

    def calculate_farmer_trade(self, mob: Dict, mob_amount: int) -> Dict:
        """Calculate what the farmer trade gives."""
        rarity = mob["rarity"]
        value_per = FARMER_EMERALD_VALUES[rarity]
        emeralds = mob_amount * value_per

        return {"mob": mob, "mob_amount": mob_amount, "emeralds": emeralds, "value_per": value_per}

    def perform_farmer_trade(
        self, session_factory, guild_id: int, user_id: int, mob_id: str, mob_amount: int, emeralds: int
    ) -> Dict:
        """Perform the farmer trade."""
        # Remove mobs from collection
        CollectionDB.remove_mob(session_factory, guild_id, user_id, mob_id, mob_amount)
        # Add emeralds
        UserDB.add_emeralds(session_factory, guild_id, user_id, emeralds)
        # Track stats
        UserDB.increment_total_farmer_trades(session_factory, guild_id, user_id)
        UserDB.add_emeralds_gained(session_factory, guild_id, user_id, emeralds)

        return {"success": True}

    def can_trade_with_cleric(self, session_factory, guild_id: int, user_id: int, mob_id: str, mob_amount: int) -> Dict:
        """Check if user can trade with cleric."""
        user = UserDB.get_user(session_factory, guild_id, user_id)
        user_trading_hall_level = user.trading_hall_level if user else 0

        if user_trading_hall_level < self.villagers["cleric"]["level"]:
            return {
                "can_trade": False,
                "error": "Your village doesn't have a Cleric yet! Upgrade your Trading Hall to trade your duplicate mobs for tokens!",
            }

        mob = self.mobs.get(mob_id)
        if not mob:
            return {"can_trade": False, "error": "That mob does not exist."}

        user_mob_count = CollectionDB.get_mob_count(session_factory, guild_id, user_id, mob_id) or 0
        if user_mob_count <= 2:
            return {
                "can_trade": False,
                "error": "You need **at least 2 duplicate copies** of this mob to trade with the Cleric.\n_The Cleric converts duplicates into tokens (2 mobs → 1 token)._",
            }

        if mob_amount >= user_mob_count:
            return {
                "can_trade": False,
                "error": f"You must keep **at least 1 copy** of each mob.\nYou can trade **up to {user_mob_count - 1}** of this mob.",
            }

        if mob_amount % 2 != 0:
            return {
                "can_trade": False,
                "error": "The Cleric only accepts **pairs of duplicates**.\n_Trade 2 mobs to receive 1 roll token._",
            }

        return {"can_trade": True, "mob": mob}

    def calculate_cleric_trade(self, mob: Dict, mob_amount: int) -> Dict:
        """Calculate what the cleric trade gives."""
        mob_rarity = mob["rarity"]
        token_rarity = CLERIC_RARITY_TO_TOKEN[mob_rarity]
        token_id = token_rarity
        token_count = mob_amount // 2
        token = self.items[token_id]

        return {"mob": mob, "mob_amount": mob_amount, "token": token, "token_id": token_id, "token_count": token_count}

    def perform_cleric_trade(
        self,
        session_factory,
        guild_id: int,
        user_id: int,
        mob_id: str,
        mob_amount: int,
        token_id: str,
        token_count: int,
    ) -> Dict:
        """Perform the cleric trade."""
        # Remove mobs from collection
        CollectionDB.remove_mob(session_factory, guild_id, user_id, mob_id, mob_amount)
        # Add tokens to inventory
        InventoryDB.add_to_inventory(session_factory, guild_id, user_id, token_id, token_count)
        # Track stats
        UserDB.increment_total_cleric_trades(session_factory, guild_id, user_id)

        return {"success": True}
