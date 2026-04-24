from typing import Any, Dict, Optional, Tuple
from .base import RollStrategy
from database.user import User as UserDB, is_same_game_day
from utils.roll_utils import roll_random_mob


class FocusRollStrategy(RollStrategy):
    """Strategy for once-per-day focus rolls (no commons)."""

    def can_execute(self, session_factory, guild_id: int, user_id: int, now: int, value: Optional[str] = None) -> Dict[str, Any]:
        if not UserDB.is_villager_unlocked(session_factory, guild_id, user_id, "librarian"):
            return {"can_execute": False, "error": "Your village doesn't have a Librarian yet! Upgrade your Trading Hall to get one focus roll per day."}

        user = UserDB.get_user(session_factory, guild_id, user_id)
        
        # Check if already claimed today
        last_claim_at = user.last_claim_at if user else 0
        if is_same_game_day(last_claim_at, now):
            return {"can_execute": False, "error": "You've already claimed today."}

        # Check hourly cooldown (focus roll also follows standard cooldown)
        last_roll_at = user.last_roll_at if user else None
        if last_roll_at:
            elapsed = now - last_roll_at
            if elapsed < 3600:
                minutes = (3600 - elapsed) // 60
                msg = f"You can roll again in **{minutes} minutes**." if minutes > 0 else "You can roll again in less than a minute."
                return {"can_execute": False, "error": msg}

        # Check if focus roll already used today
        if UserDB.has_focus_rolled_today(session_factory, guild_id, user_id, now):
            return {"can_execute": False, "error": "You've already focus rolled today."}

        return {"can_execute": True}

    def execute(self, session_factory, guild_id: int, user_id: int, now: int, value: Optional[str] = None) -> Tuple[str, Dict]:
        UserDB.record_focus_roll(session_factory, guild_id, user_id, now)
        UserDB.record_roll(session_factory, guild_id, user_id, now)
        UserDB.increment_total_rolls(session_factory, guild_id, user_id)
        
        # Exclude common rarity
        return roll_random_mob(self.mobs, self.mobs_by_rarity, exclude={"Common"})
