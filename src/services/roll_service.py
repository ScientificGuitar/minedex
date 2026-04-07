import random
from typing import Any, Dict, List, Optional, Tuple

from constants import RARITY_EMERALD_REWARDS, RARITY_WEIGHTS, VALID_TOKEN_RARITIES
from database.collection import Collection as CollectionDB
from database.inventory import Inventory as InventoryDB
from database.user import User as UserDB
from database.user import same_utc_day


class RollService:
    def __init__(self, mobs: Dict[str, Dict], mobs_by_rarity: Dict[str, List[str]], villagers: Dict[str, Dict]):
        self.mobs = mobs
        self.mobs_by_rarity = mobs_by_rarity
        self.villagers = villagers

    def can_reroll(self, session_factory, guild_id: int, user_id: int, now: int) -> Dict[str, Any]:
        """Check if user can reroll and return result."""
        user = UserDB.get_user(session_factory, guild_id, user_id)

        user_trading_hall_level = user.trading_hall_level if user else 0
        if user_trading_hall_level < self.villagers["toolsmith"]["level"]:
            return {
                "can_reroll": False,
                "error": "Your village doesn't have a Toolsmith yet! Upgrade your Trading Hall to get one reroll per day.",
            }

        last_claim_at = user.last_claim_at if user else 0
        user_tz = user.timezone if user else None
        if same_utc_day(last_claim_at, now, user_tz):
            return {"can_reroll": False, "error": "You've already claimed today."}

        last_reroll_at = user.last_reroll_at if user else 0
        if same_utc_day(last_reroll_at, now, user_tz):
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
        user = UserDB.get_user(session_factory, guild_id, user_id)

        if mode == "focus":
            user_trading_hall_level = user.trading_hall_level if user else 0
            if user_trading_hall_level < self.villagers["librarian"]["level"]:
                return {
                    "can_roll": False,
                    "error": "Your village doesn't have a Librarian yet! Upgrade your Trading Hall to get one focus roll per day.",
                }
        elif mode == "token":
            if value is None:
                return {
                    "can_roll": False,
                    "error": "You must specify a token rarity (e.g. `uncommon`, `rare`, `epic`).",
                }
            if value not in VALID_TOKEN_RARITIES:
                return {
                    "can_roll": False,
                    "error": f"Invalid token rarity. Valid options: {', '.join(VALID_TOKEN_RARITIES)}",
                }
        elif mode != "standard":
            return {
                "can_roll": False,
                "error": "Invalid roll type. Try `roll`, `roll focus`, or `roll token <rarity>`.",
            }

        last_claim_at = user.last_claim_at if user else 0
        user_tz = user.timezone if user else None
        if same_utc_day(last_claim_at, now, user_tz):
            return {"can_roll": False, "error": "You've already claimed today."}

        last_roll_at = user.last_roll_at if user else None
        cooldown = self.get_cooldown_remaining(last_roll_at, now, 3600)
        if cooldown > 0:
            minutes = cooldown // 60
            if minutes == 0:
                msg = "You can roll again in less than a minute."
            else:
                msg = f"You can roll again in **{minutes} minutes**."
            return {"can_roll": False, "error": msg}

        if mode == "focus":
            if UserDB.has_focus_rolled_today(session_factory, guild_id, user_id, now):
                return {"can_roll": False, "error": "You've already focus rolled today."}
        elif mode == "token":
            inventory = InventoryDB.get_item(session_factory, guild_id, user_id, value)
            token_count = inventory.amount if inventory else 0
            if token_count <= 0:
                return {"can_roll": False, "error": "You do not have enough of that token type."}

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
        roll_exclude = None
        roll_allowed = None

        if mode == "focus":
            roll_exclude = {"Common"}
            UserDB.record_focus_roll(session_factory, guild_id, user_id, now)
        elif mode == "token":
            InventoryDB.add_to_inventory(session_factory, guild_id, user_id, value, -1)
            roll_allowed = {value.capitalize()}
            UserDB.record_roll(session_factory, guild_id, user_id, now)
        else:
            UserDB.record_roll(session_factory, guild_id, user_id, now)

        mob_id, mob = self.roll_random_mob(exclude=roll_exclude, allowed=roll_allowed)
        return mob_id, mob

    def claim_mob(self, session_factory, guild_id: int, user_id: int, mob_id: str, mob: Dict, now: int) -> int:
        """Claim a mob and give rewards."""
        reward = RARITY_EMERALD_REWARDS[mob["rarity"]]

        CollectionDB.add_to_collection(session_factory, guild_id, user_id, mob_id)
        UserDB.update_last_claim_at(session_factory, guild_id, user_id, now)
        UserDB.add_emeralds(session_factory, guild_id, user_id, reward)

        return reward

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
