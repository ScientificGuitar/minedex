from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class RollStrategy(ABC):
    """Base class for all roll strategies."""

    def __init__(self, mobs: Dict[str, Dict], mobs_by_rarity: Dict[str, list[str]], items: Dict[str, Dict]):
        self.mobs = mobs
        self.mobs_by_rarity = mobs_by_rarity
        self.items = items

    @abstractmethod
    def can_execute(self, session_factory, guild_id: int, user_id: int, now: int, value: Optional[str] = None) -> Dict[str, Any]:
        """Check if the strategy can be executed."""
        pass

    @abstractmethod
    def execute(self, session_factory, guild_id: int, user_id: int, now: int, value: Optional[str] = None) -> Tuple[str, Dict]:
        """Execute the roll logic and return (mob_id, mob_data)."""
        pass
