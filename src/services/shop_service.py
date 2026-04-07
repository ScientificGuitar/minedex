from typing import Dict, Optional

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
        current_level = User.get_trading_hall_level(session_factory, guild_id, user_id) or 0
        emeralds = self.get_user_emeralds(session_factory, guild_id, user_id)

        villagers_data = []
        for villager_id in TRADING_HALL_ORDER:
            villager = self.villagers[villager_id]
            state = self._get_villager_state(current_level, villager["level"])
            villagers_data.append(
                {
                    "id": villager_id,
                    "name": villager["name"],
                    "description": villager["description"],
                    "price": villager["price"],
                    "state": state,
                }
            )

        return {"current_level": current_level, "emeralds": emeralds, "villagers": villagers_data}

    def get_upgrade_data(self, session_factory, guild_id: int, user_id: int, target: Optional[str] = None) -> Dict:
        """Get data for upgrade display."""
        emeralds = self.get_user_emeralds(session_factory, guild_id, user_id)
        current_level = User.get_trading_hall_level(session_factory, guild_id, user_id) or 0

        if target == "trading":
            next_level = current_level + 1
            next_villager = self._get_villager_by_level(next_level)

            if not next_villager:
                return {"error": "Trading Hall is already fully upgraded."}

            return {
                "type": "trading_hall_upgrade",
                "current_level": current_level,
                "next_level": next_level,
                "next_villager": next_villager,
                "price": next_villager["price"],
                "can_afford": emeralds >= next_villager["price"],
            }
        else:
            # General upgrade list
            next_trading_villager = self._get_villager_by_level(current_level + 1)
            return {
                "type": "upgrade_list",
                "emeralds": emeralds,
                "next_trading_villager": next_trading_villager,
                "invalid_target": target,
            }

    def can_upgrade_trading_hall(self, session_factory, guild_id: int, user_id: int) -> Dict:
        """Check if user can upgrade trading hall."""
        current_level = User.get_trading_hall_level(session_factory, guild_id, user_id) or 0
        emeralds = self.get_user_emeralds(session_factory, guild_id, user_id)

        next_villager = self._get_villager_by_level(current_level + 1)
        if not next_villager:
            return {"can_upgrade": False, "error": "Trading Hall is already fully upgraded."}

        price = next_villager["price"]
        if emeralds < price:
            return {"can_upgrade": False, "error": f"You need {price} emeralds, but you only have {emeralds}."}

        return {"can_upgrade": True, "next_villager": next_villager}

    def perform_trading_hall_upgrade(self, session_factory, guild_id: int, user_id: int) -> Dict:
        """Perform trading hall upgrade."""
        check_result = self.can_upgrade_trading_hall(session_factory, guild_id, user_id)
        if not check_result["can_upgrade"]:
            return {"success": False, "error": check_result["error"]}

        next_villager = check_result["next_villager"]
        price = next_villager["price"]

        User.add_emeralds(session_factory, guild_id, user_id, -price)
        User.upgrade_trading_hall(session_factory, guild_id, user_id)

        return {"success": True, "upgraded_to": next_villager}

    def _get_villager_state(self, current_level: int, villager_level: int) -> str:
        """Get the state of a villager relative to current level."""
        if villager_level <= current_level:
            return "owned"
        elif villager_level == current_level + 1:
            return "available"
        else:
            return "locked"

    def _get_villager_by_level(self, level: int) -> Optional[Dict]:
        """Get villager by level."""
        for _, villager in self.villagers.items():
            if villager["level"] == level:
                return villager
        return None
