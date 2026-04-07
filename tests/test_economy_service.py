"""Tests for EconomyService."""

import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.economy_service import EconomyService


class TestEconomyService:
    """Test suite for EconomyService."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_service(self, mock_mobs, mock_mobs_by_rarity, mock_items, request):
        """Set up service once per class using request fixture."""
        request.cls.service = EconomyService(mock_mobs, mock_mobs_by_rarity, mock_items)

    def test_get_user_balance(self, mock_session_factory):
        """Test getting user's emerald balance."""
        with patch("services.economy_service.UserDB.get_emeralds", return_value=150):
            balance = self.service.get_user_balance(mock_session_factory, 123, 456)

        assert balance == 150

    def test_get_user_balance_none(self, mock_session_factory):
        """Test getting balance when user has no emeralds."""
        with patch("services.economy_service.UserDB.get_emeralds", return_value=None):
            balance = self.service.get_user_balance(mock_session_factory, 123, 456)

        assert balance is None

    def test_claim_daily_reward(self, mock_session_factory, mock_user_factory):
        """Test claiming daily reward."""
        user = mock_user_factory(last_daily_at=None)
        with (
            patch("services.economy_service.UserDB.get_user", return_value=user),
            patch("services.economy_service.UserDB.update_last_daily_at"),
            patch("services.economy_service.UserDB.add_emeralds"),
            patch("services.economy_service.CollectionDB.add_to_collection"),
        ):
            result = self.service.claim_daily_reward(mock_session_factory, 123, 456, int(time.time()))

            assert "emeralds" in result
            assert result["emeralds"] in [2, 3, 4, 5]
            assert "mob" in result

    def test_get_inventory(self, mock_session_factory):
        """Test getting user inventory."""
        mock_inventory_items = [SimpleNamespace(item_id=list(self.service.items.keys())[0], amount=2)]

        with patch("services.economy_service.InventoryDB.get_items", return_value=mock_inventory_items):
            inventory = self.service.get_user_inventory(mock_session_factory, 123, 456)

            assert isinstance(inventory, dict)
            # Should have grouped items by type
            total_items = sum(len(v) for v in inventory.values())
            assert total_items > 0

    def test_get_item_info(self, mock_items):
        """Test getting item information."""
        item_id = list(mock_items.keys())[0]
        item = self.service.get_item_info(item_id)

        assert item is not None
        assert "name" in item
        assert "type" in item

    def test_get_item_info_not_found(self):
        """Test getting non-existent item information."""
        item = self.service.get_item_info("nonexistent_item_xyz")
        assert item is None

    def test_roll_random_mob(self):
        """Test rolling a random mob."""
        mob_id, mob = self.service.roll_random_mob(allowed={"Common"})

        assert mob_id in self.service.mobs
        assert mob == self.service.mobs[mob_id]

    def test_claim_daily_reward_already_claimed(self, mock_session_factory, mock_user_factory):
        """Test claiming daily reward when already claimed today."""
        now = int(time.time())
        user = mock_user_factory(last_daily_at=now - 3600)  # Claimed 1 hour ago (same day)
        with patch("services.economy_service.UserDB.get_user", return_value=user):
            result = self.service.claim_daily_reward(mock_session_factory, 123, 456, now)

        assert "error" in result
        assert "already claimed" in result["error"]

    def test_get_inventory_with_zero_amount_items(self, mock_session_factory):
        """Test getting inventory with items that have zero or negative amounts."""
        # Include items with zero/negative amounts and invalid item IDs
        mock_inventory_items = [
            SimpleNamespace(item_id=list(self.service.items.keys())[0], amount=2),  # Valid item
            SimpleNamespace(item_id="nonexistent_item", amount=1),  # Invalid item ID
            SimpleNamespace(item_id=list(self.service.items.keys())[1], amount=0),  # Zero amount
            SimpleNamespace(item_id=list(self.service.items.keys())[2], amount=-1),  # Negative amount
        ]

        with patch("services.economy_service.InventoryDB.get_items", return_value=mock_inventory_items):
            inventory = self.service.get_user_inventory(mock_session_factory, 123, 456)

            assert isinstance(inventory, dict)
            # Should only include valid items with positive amounts
            total_items = sum(len(v) for v in inventory.values())
            assert total_items == 1  # Only the first valid item should be included

    def test_roll_random_mob_with_exclude(self):
        """Test rolling random mob with excluded rarities."""
        mob_id, mob = self.service.roll_random_mob(exclude={"Legendary", "Epic"})

        assert mob["rarity"] not in {"Legendary", "Epic"}
        assert mob_id in self.service.mobs

    def test_get_item_info_with_special_characters(self):
        """Test getting item info with edge case IDs."""
        # Test with non-existent ID that has special chars
        item = self.service.get_item_info("item_with_underscore_123")
        assert item is None

    def test_get_item_info(self, mock_mobs, mock_mobs_by_rarity, mock_items):
        """Test getting item information."""
        service = EconomyService(mock_mobs, mock_mobs_by_rarity, mock_items)
        item = service.get_item_info("epic")

        assert item["name"] == "Epic Roll Token"
        assert item["type"] == "token"
        assert item["rarity"] == "Epic"

        # Test non-existing item
        item = service.get_item_info("nonexistent")
        assert item is None
