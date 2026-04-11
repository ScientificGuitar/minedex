"""
Achievement evaluation service.

Handles checking and unlocking achievements based on player state.
"""

from collections import defaultdict
from typing import Any, Dict, List

from achievements.definitions import ACHIEVEMENT_BY_ID, get_achievement, get_achievements_by_trigger
from database.achievement import AchievementDB
from database.collection import Collection as CollectionDB
from database.user import User as UserDB


class PlayerSnapshot:
    """Snapshot of player state for achievement evaluation."""

    def __init__(self, session_factory, guild_id: int, user_id: int, mobs: Dict[str, Dict]):
        self.guild_id = guild_id
        self.user_id = user_id
        self.mobs = mobs

        # Load user data
        user = UserDB.get_user(session_factory, guild_id, user_id)
        self.emeralds = user.emeralds if user else 0
        self.trading_hall_level = user.trading_hall_level if user else 0

        # Lifetime statistics
        self.total_rolls = user.total_rolls if user else 0
        self.total_claims = user.total_claims if user else 0
        self.total_farmer_trades = user.total_farmer_trades if user else 0
        self.total_cleric_trades = user.total_cleric_trades if user else 0
        self.total_emeralds_gained = user.total_emeralds_gained if user else 0
        self.total_trades = self.total_farmer_trades + self.total_cleric_trades

        # Load collection data
        collection_rows = CollectionDB.get_collection(session_factory, guild_id, user_id)
        self.collection = {row["mob_id"]: row["amount"] for row in collection_rows}
        self.unique_mobs = set(self.collection.keys())
        self.total_unique = len(self.unique_mobs)

        # Group mobs by rarity
        self.mobs_by_rarity = defaultdict(set)
        for mob_id in self.unique_mobs:
            if mob_id in mobs:
                rarity = mobs[mob_id]["rarity"]
                self.mobs_by_rarity[rarity].add(mob_id)

        # Group mobs by tags
        self.mobs_by_tag = defaultdict(set)
        for mob_id in self.unique_mobs:
            if mob_id in mobs:
                mob_data = mobs[mob_id]
                tags = mob_data.get("tags", [])
                for tag in tags:
                    self.mobs_by_tag[tag].add(mob_id)


class AchievementService:
    """Service for evaluating and unlocking achievements."""

    def __init__(self, mobs: Dict[str, Dict], mobs_by_rarity: Dict[str, List[str]]):
        self.mobs = mobs
        self.mobs_by_rarity = mobs_by_rarity

        # Set up achievement check functions
        self._setup_checks()

    def _setup_checks(self):
        """Set up the check functions for all achievements."""
        # Collection achievements
        ACHIEVEMENT_BY_ID["first_mob"].check = lambda s: s.total_unique >= 1
        ACHIEVEMENT_BY_ID["unique_10"].check = lambda s: s.total_unique >= 10
        ACHIEVEMENT_BY_ID["unique_25"].check = lambda s: s.total_unique >= 25
        ACHIEVEMENT_BY_ID["unique_50"].check = lambda s: s.total_unique >= 50
        ACHIEVEMENT_BY_ID["unique_100"].check = lambda s: s.total_unique >= 100

        ACHIEVEMENT_BY_ID["first_legendary"].check = lambda s: len(s.mobs_by_rarity["Legendary"]) >= 1

        # Rarity completion achievements
        for rarity in ["Common", "Uncommon", "Rare", "Epic", "Legendary"]:
            achievement_id = f"complete_{rarity.lower()}"
            expected_count = len(self.mobs_by_rarity.get(rarity, []))
            ACHIEVEMENT_BY_ID[achievement_id].check = lambda s, r=rarity, c=expected_count: (
                len(s.mobs_by_rarity[r]) >= c
            )

        # World completion achievements
        overworld_mobs = sum(1 for mob_id, mob in self.mobs.items() if "overworld" in mob.get("tags", []))
        ACHIEVEMENT_BY_ID["complete_overworld"].check = lambda s, count=overworld_mobs: (
            len(s.mobs_by_tag["overworld"]) >= count if count > 0 else False
        )

        nether_mobs = sum(1 for mob_id, mob in self.mobs.items() if "nether" in mob.get("tags", []))
        ACHIEVEMENT_BY_ID["complete_nether"].check = lambda s, count=nether_mobs: (
            len(s.mobs_by_tag["nether"]) >= count if count > 0 else False
        )

        end_mobs = sum(1 for mob_id, mob in self.mobs.items() if "end" in mob.get("tags", []))
        ACHIEVEMENT_BY_ID["complete_end"].check = lambda s, count=end_mobs: (
            len(s.mobs_by_tag["end"]) >= count if count > 0 else False
        )

        # Boss hunter
        ACHIEVEMENT_BY_ID["boss_hunter"].check = lambda s: "ender_dragon" in s.unique_mobs and "wither" in s.unique_mobs

        # Full collection
        total_mobs = len(self.mobs)
        ACHIEVEMENT_BY_ID["full_collection"].check = lambda s, t=total_mobs: s.total_unique >= t

        # Trading achievements
        ACHIEVEMENT_BY_ID["first_trade"].check = lambda s: s.total_trades >= 1

        # Economy achievements
        ACHIEVEMENT_BY_ID["emerald_1000"].check = lambda s: s.emeralds >= 1000
        ACHIEVEMENT_BY_ID["emerald_10000"].check = lambda s: s.emeralds >= 10000

        # Lifetime statistics achievements
        ACHIEVEMENT_BY_ID["roller_10"].check = lambda s: s.total_rolls >= 10
        ACHIEVEMENT_BY_ID["roller_100"].check = lambda s: s.total_rolls >= 100
        ACHIEVEMENT_BY_ID["roller_1000"].check = lambda s: s.total_rolls >= 1000

        ACHIEVEMENT_BY_ID["claimer_50"].check = lambda s: s.total_claims >= 50
        ACHIEVEMENT_BY_ID["claimer_250"].check = lambda s: s.total_claims >= 250

        ACHIEVEMENT_BY_ID["trader_5"].check = lambda s: s.total_trades >= 5
        ACHIEVEMENT_BY_ID["trader_50"].check = lambda s: s.total_trades >= 50
        ACHIEVEMENT_BY_ID["trader_100"].check = lambda s: s.total_trades >= 100
        ACHIEVEMENT_BY_ID["trader_1000"].check = lambda s: s.total_trades >= 1000

        ACHIEVEMENT_BY_ID["emeralds_earned_5000"].check = lambda s: s.total_emeralds_gained >= 5000
        ACHIEVEMENT_BY_ID["emeralds_earned_50000"].check = lambda s: s.total_emeralds_gained >= 50000

    def evaluate_unlocked(
        self, session_factory, guild_id: int, user_id: int, trigger: str, now: int
    ) -> List[Dict[str, Any]]:
        """
        Evaluate achievements for a trigger and return newly unlocked ones.

        Returns list of achievement dicts that were just unlocked.
        """
        # Get achievements to check for this trigger
        achievements_to_check = get_achievements_by_trigger(trigger)
        if not achievements_to_check:
            return []

        # Get current unlocked achievements
        unlocked_ids = self._get_unlocked_achievement_ids(session_factory, guild_id, user_id)

        # Create player snapshot
        snapshot = PlayerSnapshot(session_factory, guild_id, user_id, self.mobs)

        # Check each achievement
        newly_unlocked = []
        for achievement in achievements_to_check:
            if achievement.id in unlocked_ids:
                continue  # Already unlocked

            if achievement.check(snapshot):
                # Unlock the achievement
                self._unlock_achievement(session_factory, guild_id, user_id, achievement.id, now)
                newly_unlocked.append(
                    {
                        "id": achievement.id,
                        "name": achievement.name,
                        "description": achievement.description,
                        "category": achievement.category,
                        "hidden": achievement.hidden,
                    }
                )

        return newly_unlocked

    def _get_unlocked_achievement_ids(self, session_factory, guild_id: int, user_id: int) -> set[str]:
        """Get set of already unlocked achievement IDs for a user."""
        unlocks = AchievementDB.get_user_achievements(session_factory, guild_id, user_id)
        return {unlock["achievement_id"] for unlock in unlocks}

    def _unlock_achievement(self, session_factory, guild_id: int, user_id: int, achievement_id: str, now: int):
        """Unlock an achievement for a user."""
        AchievementDB.unlock_achievement(session_factory, guild_id, user_id, achievement_id, now)

    def get_user_achievements(self, session_factory, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get all unlocked achievements for a user."""
        unlocks = AchievementDB.get_user_achievements(session_factory, guild_id, user_id)

        achievements = []
        for unlock in unlocks:
            achievement = get_achievement(unlock["achievement_id"])
            if achievement:
                achievements.append(
                    {
                        "id": achievement.id,
                        "name": achievement.name,
                        "description": achievement.description,
                        "category": achievement.category,
                        "unlocked_at": unlock["unlocked_at"],
                        "hidden": achievement.hidden,
                    }
                )

        return achievements

    def get_user_stats(self, session_factory, guild_id: int, user_id: int) -> Dict[str, Any]:
        """Get lifetime statistics for a user (for stats command)."""
        snapshot = PlayerSnapshot(session_factory, guild_id, user_id, self.mobs)

        return {
            "unique_mobs": snapshot.total_unique,
            "total_mobs": len(self.mobs),
            "emeralds": snapshot.emeralds,
            "trading_hall_level": snapshot.trading_hall_level,
            "collection_completion": snapshot.total_unique / len(self.mobs) * 100,
            "total_rolls": snapshot.total_rolls,
            "total_claims": snapshot.total_claims,
            "total_farmer_trades": snapshot.total_farmer_trades,
            "total_cleric_trades": snapshot.total_cleric_trades,
            "total_trades": snapshot.total_trades,
            "total_emeralds_gained": snapshot.total_emeralds_gained,
        }
