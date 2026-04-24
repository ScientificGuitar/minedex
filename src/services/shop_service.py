from typing import Any, Dict, List, Optional

from database.inventory import Inventory as InventoryDB
from database.user import User


class ShopService:
    def __init__(self, shop_data: Dict):
        self.shop_data = shop_data

    def get_user_emeralds(self, session_factory, guild_id: int, user_id: int) -> int:
        """Get user's emerald balance."""
        return User.get_emeralds(session_factory, guild_id, user_id) or 0

    def get_shop_inventory(self, session_factory, guild_id: int, user_id: int, category: str) -> Dict[str, Any]:
        """Get inventory for a specific shop category."""
        if category not in self.shop_data:
            return {"error": f"Invalid shop category: {category}"}

        items = self.shop_data[category]
        unlocked = User.get_unlocked_villagers(session_factory, guild_id, user_id)
        emeralds = self.get_user_emeralds(session_factory, guild_id, user_id)

        processed_items = []
        for item_id, item_data in items.items():
            # 1. Skip owned permanent upgrades (Don't show what you already bought)
            if category == "permanent_upgrades" and item_id in unlocked:
                continue

            # 2. Check requirements
            unmet_reqs = [req for req in item_data.get("requirements", []) if req not in unlocked]
            
            # 3. Only show items that are available to buy (no unmet requirements)
            # This creates a "discovery" progression feel.
            if not unmet_reqs:
                processed_items.append({
                    "id": item_id,
                    "name": item_data["name"],
                    "description": item_data["description"],
                    "price": item_data["price"],
                    "state": "available",
                    "type": item_data.get("type")
                })

        return {
            "category": category,
            "emeralds": emeralds,
            "items": processed_items
        }

    def can_purchase(self, session_factory, guild_id: int, user_id: int, item_id: str, category: str) -> Dict[str, Any]:
        """Check if a user can purchase an item."""
        if category not in self.shop_data or item_id not in self.shop_data[category]:
            return {"can_purchase": False, "error": "Item not found."}

        item_data = self.shop_data[category][item_id]
        emeralds = self.get_user_emeralds(session_factory, guild_id, user_id)
        unlocked = User.get_unlocked_villagers(session_factory, guild_id, user_id)

        # 1. Emerald check
        if emeralds < item_data["price"]:
            return {
                "can_purchase": False, 
                "error": f"You need {item_data['price']} emeralds, but you only have {emeralds}."
            }

        # 2. Permanent ownership check
        if category == "permanent_upgrades" and item_id in unlocked:
            return {"can_purchase": False, "error": "You already own this upgrade."}

        # 3. Requirements check
        for req_id in item_data.get("requirements", []):
            if req_id not in unlocked:
                req_item = self.shop_data[category].get(req_id, {"name": req_id})
                return {
                    "can_purchase": False, 
                    "error": f"You must first unlock: {req_item['name']}"
                }

        return {"can_purchase": True, "item": item_data}

    def perform_purchase(self, session_factory, guild_id: int, user_id: int, item_id: str, category: str) -> Dict[str, Any]:
        """Execute the purchase logic."""
        check = self.can_purchase(session_factory, guild_id, user_id, item_id, category)
        if not check["can_purchase"]:
            return {"success": False, "error": check["error"]}

        item_data = check["item"]
        price = item_data["price"]

        # Deduct emeralds
        User.add_emeralds(session_factory, guild_id, user_id, -price)

        # Apply effects
        if category == "permanent_upgrades":
            User.unlock_villager(session_factory, guild_id, user_id, item_id)
        elif category == "consumables":
            # Assuming consumables are currently just tokens
            if item_data["type"] == "token":
                InventoryDB.add_to_inventory(session_factory, guild_id, user_id, item_data["item_id"], 1)

        return {"success": True, "item": item_data}
