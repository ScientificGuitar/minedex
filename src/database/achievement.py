"""
Database operations for achievements.
"""

from typing import Any, Dict, List

from database.db import AchievementUnlock as AchievementUnlockModel


class AchievementDB:
    """Database operations for achievements."""

    @staticmethod
    def get_user_achievements(session_factory, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get all unlocked achievements for a user."""
        with session_factory() as session:
            unlocks = (
                session.query(AchievementUnlockModel)
                .filter_by(guild_id=guild_id, user_id=user_id)
                .order_by(AchievementUnlockModel.unlocked_at)
                .all()
            )

            return [
                {
                    "achievement_id": unlock.achievement_id,
                    "unlocked_at": unlock.unlocked_at,
                }
                for unlock in unlocks
            ]

    @staticmethod
    def unlock_achievement(session_factory, guild_id: int, user_id: int, achievement_id: str, unlocked_at: int):
        """Unlock an achievement for a user."""
        with session_factory() as session:
            # Check if already unlocked (shouldn't happen, but safety check)
            existing = (
                session.query(AchievementUnlockModel)
                .filter_by(guild_id=guild_id, user_id=user_id, achievement_id=achievement_id)
                .first()
            )

            if not existing:
                unlock = AchievementUnlockModel(
                    guild_id=guild_id,
                    user_id=user_id,
                    achievement_id=achievement_id,
                    unlocked_at=unlocked_at,
                )
                session.add(unlock)
                session.commit()
