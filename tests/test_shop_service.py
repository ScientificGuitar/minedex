"""Tests for ShopService."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.shop_service import ShopService


class TestShopService:
    """Test suite for ShopService."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_service(self, mock_shop_data, request):
        """Set up service once per class using request fixture."""
        request.cls.service = ShopService(mock_shop_data)

    def test_get_user_emeralds(self, mock_session_factory):
        """Test getting user's emerald count."""
        with patch("services.shop_service.User.get_emeralds", return_value=500):
            emeralds = self.service.get_user_emeralds(mock_session_factory, 123, 456)

        assert emeralds == 500

    def test_get_shop_inventory(self, mock_session_factory):
        """Test getting shop inventory for a category."""
        with (
            patch("services.shop_service.User.get_unlocked_villagers", return_value=[]),
            patch("services.shop_service.User.get_emeralds", return_value=500)
        ):
            inventory = self.service.get_shop_inventory(mock_session_factory, 123, 456, "permanent_upgrades")

        assert inventory["category"] == "permanent_upgrades"
        assert inventory["emeralds"] == 500
        assert len(inventory["items"]) > 0
        assert inventory["items"][0]["state"] == "available"

    def test_can_purchase_success(self, mock_session_factory):
        """Test successful purchase check."""
        with (
            patch("services.shop_service.User.get_unlocked_villagers", return_value=[]),
            patch("services.shop_service.User.get_emeralds", return_value=500)
        ):
            result = self.service.can_purchase(mock_session_factory, 123, 456, "farmer", "permanent_upgrades")

        assert result["can_purchase"] is True
        assert result["item"]["name"] == "Farmer"

    def test_can_purchase_insufficient_emeralds(self, mock_session_factory):
        """Test purchase check with insufficient emeralds."""
        with (
            patch("services.shop_service.User.get_unlocked_villagers", return_value=[]),
            patch("services.shop_service.User.get_emeralds", return_value=10)
        ):
            result = self.service.can_purchase(mock_session_factory, 123, 456, "farmer", "permanent_upgrades")

        assert result["can_purchase"] is False
        assert "emeralds" in result["error"]

    def test_can_purchase_missing_requirements(self, mock_session_factory):
        """Test purchase check with missing requirements."""
        with (
            patch("services.shop_service.User.get_unlocked_villagers", return_value=[]),
            patch("services.shop_service.User.get_emeralds", return_value=500)
        ):
            # Cleric requires farmer
            result = self.service.can_purchase(mock_session_factory, 123, 456, "cleric", "permanent_upgrades")

        assert result["can_purchase"] is False
        assert "unlock" in result["error"]

    def test_can_purchase_already_owned(self, mock_session_factory):
        """Test purchase check when already owned."""
        with (
            patch("services.shop_service.User.get_unlocked_villagers", return_value=["farmer"]),
            patch("services.shop_service.User.get_emeralds", return_value=500)
        ):
            result = self.service.can_purchase(mock_session_factory, 123, 456, "farmer", "permanent_upgrades")

        assert result["can_purchase"] is False
        assert "already own" in result["error"]

    def test_perform_purchase_upgrade(self, mock_session_factory):
        """Test performing an upgrade purchase."""
        with (
            patch("services.shop_service.User.get_unlocked_villagers", return_value=[]),
            patch("services.shop_service.User.get_emeralds", return_value=500),
            patch("services.shop_service.User.add_emeralds") as mock_add_em,
            patch("services.shop_service.User.unlock_villager") as mock_unlock
        ):
            result = self.service.perform_purchase(mock_session_factory, 123, 456, "farmer", "permanent_upgrades")

        assert result["success"] is True
        mock_add_em.assert_called_once() # Deduct price
        mock_unlock.assert_called_once_with(mock_session_factory, 123, 456, "farmer")

    def test_perform_purchase_consumable(self, mock_session_factory):
        """Test performing a consumable purchase."""
        with (
            patch("services.shop_service.User.get_unlocked_villagers", return_value=[]),
            patch("services.shop_service.User.get_emeralds", return_value=500),
            patch("services.shop_service.User.add_emeralds"),
            patch("services.shop_service.InventoryDB.add_to_inventory") as mock_add_inv
        ):
            result = self.service.perform_purchase(mock_session_factory, 123, 456, "token", "consumables")

        assert result["success"] is True
        mock_add_inv.assert_called_once()
