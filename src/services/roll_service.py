import random
from typing import Any, Dict, List, Optional, Tuple

from constants import RARITY_WEIGHTS, VALID_TOKEN_RARITIES
from database.collection import Collection as CollectionDB
from database.inventory import Inventory as InventoryDB
from database.user import User as UserDB, is_same_game_day
from strategies.standard import StandardRollStrategy
from strategies.token import TokenRollStrategy
from strategies.focus import FocusRollStrategy
from utils.roll_utils import roll_random_mob as utils_roll_random_mob


class RollService:
    def __init__(self, mobs: Dict[str, Dict], mobs_by_rarity: Dict[str, List[str]], villagers: Dict[str, Dict], items: Dict[str, Dict]):
        self.mobs = mobs
        self.mobs_by_rarity = mobs_by_rarity
        self.villagers = villagers
        self.items = items
        
        # Strategy mapping
        self._strategies = {
            "standard": StandardRollStrategy(mobs, mobs_by_rarity, items),
            "token": TokenRollStrategy(mobs, mobs_by_rarity, items),
            "focus": FocusRollStrategy(mobs, mobs_by_rarity, items)
        }

    def can_reroll(self, session_factory, guild_id: int, user_id: int, now: int) -> Dict[str, Any]:
        """Check if user can reroll and return result."""
        if not UserDB.is_villager_unlocked(session_factory, guild_id, user_id, "toolsmith"):
            return {
                "can_reroll": False,
                "error": "Your village doesn't have a Toolsmith yet! Upgrade your Trading Hall to get one reroll per day.",
            }

        user = UserDB.get_user(session_factory, guild_id, user_id)

        last_claim_at = user.last_claim_at if user else 0
        if is_same_game_day(last_claim_at, now):
            return {"can_reroll": False, "error": "You've already claimed today."}

        last_reroll_at = user.last_reroll_at if user else 0
        if is_same_game_day(last_reroll_at, now):
            return {"can_reroll": False, "error": "You've already rerolled today."}

        return {"can_reroll": True}

    def perform_reroll(self, session_factory, guild_id: int, user_id: int, now: int) -> Tuple[str, Dict]:
        """Perform a reroll and return the mob."""
        mob_id, mob = self.roll_random_mob()
        UserDB.record_reroll(session_factory, guild_id, user_id, now)
        return mob_id, mob

    def can_roll(
        self,
        session_factory,
        guild_id: int,
        user_id: int,
        now: int,
        mode: str = "standard",
        value: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check if user can perform a roll and return result."""
        strategy = self._strategies.get(mode)
        if not strategy:
            return {
                "can_roll": False,
                "error": "Invalid roll type. Try `roll`, `roll focus`, or `roll token <rarity>`.",
            }

        result = strategy.can_execute(session_factory, guild_id, user_id, now, value)
        if not result.get("can_execute"):
            return {"can_roll": False, "error": result.get("error")}

        return {"can_roll": True, "mode": mode, "value": value}

    def perform_roll(
        self,
        session_factory,
        guild_id: int,
        user_id: int,
        now: int,
        mode: str = "standard",
        value: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Perform a roll and return the mob."""
        strategy = self._strategies.get(mode)
        return strategy.execute(session_factory, guild_id, user_id, now, value)

    def claim_mob(self, session_factory, guild_id: int, user_id: int, mob_id: str, mob: Dict, now: int) -> int:
        """Claim a mob and give rewards."""
        reward = mob.get("claim_reward", 0)

        CollectionDB.add_to_collection(session_factory, guild_id, user_id, mob_id)
        UserDB.update_last_claim_at(session_factory, guild_id, user_id, now)
        UserDB.add_emeralds(session_factory, guild_id, user_id, reward)
        UserDB.increment_total_claims(session_factory, guild_id, user_id)
        UserDB.add_emeralds_gained(session_factory, guild_id, user_id, reward)

        return reward

    def roll_random_mob(self, exclude: Optional[set] = None, allowed: Optional[set] = None) -> Tuple[str, Dict]:
        """Roll a random mob based on rarity weights."""
        return utils_roll_random_mob(self.mobs, self.mobs_by_rarity, exclude, allowed)

    @staticmethod
    def roll_rarity(exclude: Optional[set] = None, allowed: Optional[set] = None) -> str:
        """Roll a rarity based on weights."""
        from utils.roll_utils import roll_rarity as utils_roll_rarity
        return utils_roll_rarity(exclude, allowed)

    def build_mob_embed_data(
        self, session_factory, guild_id: int, user_id: int, mob_id: str, mob: Dict, rerolled: bool = False
    ) -> Dict[str, Any]:
        """Build data for mob embed."""
        owned_amount = CollectionDB.get_mob_count(session_factory, guild_id, user_id, mob_id) or 0

        return {"mob": mob, "owned_amount": owned_amount, "rerolled": rerolled}

    @staticmethod
    def get_cooldown_remaining(last_action_ts: Optional[int], now_ts: int, cooldown_seconds: int) -> int:
        """Get remaining cooldown time."""
        if last_action_ts is None:
            return 0

        elapsed = now_ts - last_action_ts
        remaining = cooldown_seconds - elapsed
        return max(0, remaining)
