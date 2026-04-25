from typing import Any, Dict, Optional, Tuple

from constants import VALID_TOKEN_RARITIES
from database.inventory import Inventory as InventoryDB
from database.user import User as UserDB
from database.user import is_same_game_day
from utils.roll_utils import roll_random_mob

from .base import RollStrategy


class TokenRollStrategy(RollStrategy):
    """Strategy for rolls using rarity tokens."""

    def can_execute(
        self, session_factory, guild_id: int, user_id: int, now: int, value: Optional[str] = None
    ) -> Dict[str, Any]:
        if value is None:
            return {"can_execute": False, "error": "You must specify a token rarity (e.g. `uncommon`, `rare`, `epic`)."}

        if value not in VALID_TOKEN_RARITIES:
            return {
                "can_execute": False,
                "error": f"Invalid token rarity. Valid options: {', '.join(VALID_TOKEN_RARITIES)}",
            }

        user = UserDB.get_user(session_factory, guild_id, user_id)

        # Check if already claimed today
        last_claim_at = user.last_claim_at if user else 0
        if is_same_game_day(last_claim_at, now):
            return {"can_execute": False, "error": "You've already claimed today."}

        # Check inventory for token
        inventory = InventoryDB.get_item(session_factory, guild_id, user_id, value)
        token_count = inventory.amount if inventory else 0
        if token_count <= 0:
            return {"can_execute": False, "error": f"You do not have any {value.capitalize()} Roll Tokens."}

        return {"can_execute": True}

    def execute(
        self, session_factory, guild_id: int, user_id: int, now: int, value: Optional[str] = None
    ) -> Tuple[str, Dict]:
        # Consume token
        InventoryDB.add_to_inventory(session_factory, guild_id, user_id, value, -1)

        # Record roll for cooldown (tokens share standard roll timestamp to prevent stacking)
        UserDB.record_roll(session_factory, guild_id, user_id, now)
        UserDB.increment_total_rolls(session_factory, guild_id, user_id)

        # Roll restricted to token rarity
        allowed_rarity = {value.capitalize()}
        return roll_random_mob(self.mobs, self.mobs_by_rarity, allowed=allowed_rarity)
