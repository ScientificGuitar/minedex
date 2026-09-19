from typing import Dict

from database.collection import Collection as CollectionDB
from database.inventory import Inventory as InventoryDB
from database.user import User as UserDB


class TradeService:
    MASTER_CLERIC_DEFAULT_FEE = 500

    def __init__(self, mobs: Dict[str, Dict], villagers: Dict[str, Dict], items: Dict[str, Dict]):
        self.mobs = mobs
        self.villagers = villagers
        self.items = items

    def get_master_cleric_fee(self) -> int:
        """Fee in emeralds for a Master Cleric trade. Data-driven with fallback."""
        return self.villagers.get("master_cleric", {}).get("trade_fee", self.MASTER_CLERIC_DEFAULT_FEE)

    def can_trade_with_farmer(self, session_factory, guild_id: int, user_id: int, mob_id: str, mob_amount: int) -> Dict:
        """Check if user can trade with farmer."""
        if not UserDB.is_villager_unlocked(session_factory, guild_id, user_id, "farmer"):
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
        value_per = mob.get("farmer_value", 0)
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
        UserDB.add_mobs_traded(session_factory, guild_id, user_id, mob_amount)

        return {"success": True}

    def can_trade_with_cleric(self, session_factory, guild_id: int, user_id: int, mob_id: str, mob_amount: int) -> Dict:
        """Check if user can trade with cleric."""
        if not UserDB.is_villager_unlocked(session_factory, guild_id, user_id, "cleric"):
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

        if not mob.get("token_reward"):
            return {
                "can_trade": False,
                "error": "The Cleric is not interested in this mob. Some rare mobs cannot be converted into tokens.",
            }

        return {"can_trade": True, "mob": mob}

    def calculate_cleric_trade(self, mob: Dict, mob_amount: int) -> Dict:
        """Calculate what the cleric trade gives."""
        token_id = mob.get("token_reward")
        token_count = mob_amount // 2
        token = self.items.get(token_id)

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
        UserDB.add_mobs_traded(session_factory, guild_id, user_id, mob_amount)

        return {"success": True}

    def can_trade_with_master_cleric(
        self, session_factory, guild_id: int, user_id: int, mob_id: str, mob_amount: int
    ) -> Dict:
        """Check if user can trade with the Master Cleric (strict 2x same Legendary + fee)."""
        if not UserDB.is_villager_unlocked(session_factory, guild_id, user_id, "master_cleric"):
            return {
                "can_trade": False,
                "error": "Your village doesn't have a Master Cleric yet! Upgrade your Trading Hall (requires Librarian) to transmute duplicate Legendaries!",
            }

        mob = self.mobs.get(mob_id)
        if not mob:
            return {"can_trade": False, "error": "That mob does not exist."}

        if mob.get("rarity") != "Legendary" or mob.get("token_reward") != "legendary":
            return {
                "can_trade": False,
                "error": "The Master Cleric only accepts **duplicate Legendary** mobs.\n_Trade 2 copies of the same Legendary + 500 emeralds for 1 Legendary Roll Token._",
            }

        user_mob_count = CollectionDB.get_mob_count(session_factory, guild_id, user_id, mob_id) or 0
        if user_mob_count <= 2:
            return {
                "can_trade": False,
                "error": "You need **at least 2 duplicate copies** of this Legendary to trade with the Master Cleric.\n_The Master Cleric transmutes duplicates (2 mobs + fee → 1 token)._",
            }

        if mob_amount != 2:
            return {
                "can_trade": False,
                "error": "The Master Cleric only accepts **exactly 2 copies** of the same Legendary at a time.",
            }

        if mob_amount >= user_mob_count:
            return {
                "can_trade": False,
                "error": f"You must keep **at least 1 copy** of each mob.\nYou can trade **up to {user_mob_count - 1}** of this mob.",
            }

        fee = self.get_master_cleric_fee()
        emeralds = UserDB.get_emeralds(session_factory, guild_id, user_id) or 0
        if emeralds < fee:
            return {
                "can_trade": False,
                "error": f"The Master Cleric demands a fee of **{fee} emeralds**.\n_You only have {emeralds}._",
            }

        return {"can_trade": True, "mob": mob, "fee": fee}

    def calculate_master_cleric_trade(self, mob: Dict, mob_amount: int) -> Dict:
        """Calculate what the Master Cleric trade gives (uses token_reward, like Cleric)."""
        token_id = mob.get("token_reward")
        token_count = mob_amount // 2
        token = self.items.get(token_id)
        fee = self.get_master_cleric_fee()

        return {
            "mob": mob,
            "mob_amount": mob_amount,
            "token": token,
            "token_id": token_id,
            "token_count": token_count,
            "fee": fee,
        }

    def perform_master_cleric_trade(
        self,
        session_factory,
        guild_id: int,
        user_id: int,
        mob_id: str,
        mob_amount: int,
        token_id: str,
        token_count: int,
        fee: int,
    ) -> Dict:
        """Perform the Master Cleric trade: remove mobs, charge fee, grant token."""
        CollectionDB.remove_mob(session_factory, guild_id, user_id, mob_id, mob_amount)
        UserDB.add_emeralds(session_factory, guild_id, user_id, -fee)
        InventoryDB.add_to_inventory(session_factory, guild_id, user_id, token_id, token_count)
        UserDB.increment_total_cleric_trades(session_factory, guild_id, user_id)
        UserDB.add_mobs_traded(session_factory, guild_id, user_id, mob_amount)

        return {"success": True}
