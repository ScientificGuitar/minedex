from typing import Dict, List, Optional

from constants import TRADING_HALL_ORDER
from database.user import User


class ShopService:
    def __init__(self, villagers: Dict[str, Dict]):
        self.villagers = villagers

    def get_user_emeralds(self, session_factory, guild_id: int, user_id: int) -> int:
        """Get user's emerald balance."""
        return User.get_emeralds(session_factory, guild_id, user_id) or 0

    def get_trading_hall_data(self, session_factory, guild_id: int, user_id: int) -> Dict:
        """Get data for trading hall display."""
        unlocked = User.get_unlocked_villagers(session_factory, guild_id, user_id)
        emeralds = self.get_user_emeralds(session_factory, guild_id, user_id)

        villagers_data = []
        for villager_id in TRADING_HALL_ORDER:
            villager = self.villagers[villager_id]
            state = self._get_villager_state(unlocked, villager_id)
            villagers_data.append(
                {
                    "id": villager_id,
                    "name": villager["name"],
                    "description": villager["description"],
                    "price": villager["price"],
                    "state": state,
                }
            )

        return {"unlocked_count": len(unlocked), "emeralds": emeralds, "villagers": villagers_data}

    def get_upgrade_data(self, session_factory, guild_id: int, user_id: int, target: Optional[str] = None) -> Dict:
        """Get data for upgrade display."""
        emeralds = self.get_user_emeralds(session_factory, guild_id, user_id)
        unlocked = User.get_unlocked_villagers(session_factory, guild_id, user_id)

        if target == "trading":
            next_villager_id = self._get_next_available_villager_id(unlocked)

            if not next_villager_id:
                return {"error": "Trading Hall is already fully upgraded."}

            next_villager = self.villagers[next_villager_id]
            return {
                "type": "trading_hall_upgrade",
                "next_villager_id": next_villager_id,
                "next_villager": next_villager,
                "price": next_villager["price"],
                "can_afford": emeralds >= next_villager["price"],
            }
        else:
            # General upgrade list
            next_villager_id = self._get_next_available_villager_id(unlocked)
            next_trading_villager = self.villagers.get(next_villager_id) if next_villager_id else None
            return {
                "type": "upgrade_list",
                "emeralds": emeralds,
                "next_trading_villager": next_trading_villager,
                "invalid_target": target,
            }

    def can_upgrade_trading_hall(self, session_factory, guild_id: int, user_id: int) -> Dict:
        """Check if user can upgrade trading hall."""
        unlocked = User.get_unlocked_villagers(session_factory, guild_id, user_id)
        emeralds = self.get_user_emeralds(session_factory, guild_id, user_id)

        next_villager_id = self._get_next_available_villager_id(unlocked)
        if not next_villager_id:
            return {"can_upgrade": False, "error": "Trading Hall is already fully upgraded."}

        next_villager = self.villagers[next_villager_id]
        price = next_villager["price"]
        if emeralds < price:
            return {"can_upgrade": False, "error": f"You need {price} emeralds, but you only have {emeralds}."}

        return {"can_upgrade": True, "next_villager_id": next_villager_id, "next_villager": next_villager}

    def perform_trading_hall_upgrade(self, session_factory, guild_id: int, user_id: int) -> Dict:
        """Perform trading hall upgrade."""
        check_result = self.can_upgrade_trading_hall(session_factory, guild_id, user_id)
        if not check_result["can_upgrade"]:
            return {"success": False, "error": check_result["error"]}

        next_villager_id = check_result["next_villager_id"]
        next_villager = check_result["next_villager"]
        price = next_villager["price"]

        User.add_emeralds(session_factory, guild_id, user_id, -price)
        User.unlock_villager(session_factory, guild_id, user_id, next_villager_id)

        return {"success": True, "upgraded_to": next_villager}

    def _get_villager_state(self, unlocked: List[str], villager_id: str) -> str:
        """Get the state of a villager."""
        if villager_id in unlocked:
            return "owned"
        
        # Check if it's the next one in line for the linear progression part
        next_id = self._get_next_available_villager_id(unlocked)
        if villager_id == next_id:
            return "available"
        
        return "locked"

    def _get_next_available_villager_id(self, unlocked: List[str]) -> Optional[str]:
        """Get the next villager ID to unlock in the linear progression."""
        for villager_id in TRADING_HALL_ORDER:
            if villager_id not in unlocked:
                return villager_id
        return None
