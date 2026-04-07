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
    def setup_service(self, mock_villagers, request):
        """Set up service once per class using request fixture."""
        request.cls.service = ShopService(mock_villagers)

    def test_get_user_emeralds(self, mock_session_factory):
        """Test getting user's emerald count."""
        with patch("services.shop_service.User.get_emeralds", return_value=500):
            emeralds = self.service.get_user_emeralds(mock_session_factory, 123, 456)

        assert emeralds == 500

    def test_can_upgrade_trading_hall_success(self, mock_session_factory):
        """Test successful trading hall upgrade check."""
        with (
            patch("services.shop_service.User.get_trading_hall_level", return_value=0),
            patch("services.shop_service.User.get_emeralds", return_value=500),
        ):
            result = self.service.can_upgrade_trading_hall(mock_session_factory, 123, 456)

        assert result["can_upgrade"] is True

    def test_can_upgrade_trading_hall_insufficient_emeralds(self, mock_session_factory):
        """Test trading hall upgrade with insufficient emeralds."""
        with (
            patch("services.shop_service.User.get_trading_hall_level", return_value=0),
            patch("services.shop_service.User.get_emeralds", return_value=50),
        ):
            result = self.service.can_upgrade_trading_hall(mock_session_factory, 123, 456)

        assert result["can_upgrade"] is False
        assert "need" in result["error"]

    def test_can_upgrade_already_maxed(self, mock_session_factory):
        """Test upgrading when already at max level."""
        with (
            patch("services.shop_service.User.get_trading_hall_level", return_value=10),
            patch("services.shop_service.User.get_emeralds", return_value=5000),
        ):
            result = self.service.can_upgrade_trading_hall(mock_session_factory, 123, 456)

        assert result["can_upgrade"] is False
        assert "fully upgraded" in result["error"]

    def test_perform_trading_hall_upgrade_insufficient_funds(self, mock_session_factory):
        """Test performing trading hall upgrade when user can't afford it."""
        with (
            patch("services.shop_service.User.get_trading_hall_level", return_value=0),
            patch("services.shop_service.User.get_emeralds", return_value=50),  # Not enough for upgrade
        ):
            result = self.service.perform_trading_hall_upgrade(mock_session_factory, 123, 456)

        assert result["success"] is False
        assert "error" in result

    def test_get_upgrade_data(self, mock_session_factory):
        """Test getting upgrade data."""
        with (
            patch("services.shop_service.User.get_trading_hall_level", return_value=0),
            patch("services.shop_service.User.get_emeralds", return_value=500),
        ):
            data = self.service.get_upgrade_data(mock_session_factory, 123, 456, "trading")

        assert data["type"] == "trading_hall_upgrade"
        assert data["can_afford"] is True

    def test_get_trading_hall_data(self, mock_session_factory):
        """Test getting complete trading hall display data."""
        with (
            patch("services.shop_service.User.get_trading_hall_level", return_value=2),
            patch("services.shop_service.User.get_emeralds", return_value=750),
        ):
            data = self.service.get_trading_hall_data(mock_session_factory, 123, 456)

        assert data["current_level"] == 2
        assert data["emeralds"] == 750
        assert "villagers" in data
        assert len(data["villagers"]) > 0
        for villager in data["villagers"]:
            assert "id" in villager
            assert "name" in villager
            assert "description" in villager
            assert "state" in villager

    def test_get_upgrade_data_fully_upgraded(self, mock_session_factory):
        """Test get_upgrade_data when trading hall is fully upgraded."""
        with (
            patch("services.shop_service.User.get_trading_hall_level", return_value=10),
            patch("services.shop_service.User.get_emeralds", return_value=5000),
        ):
            data = self.service.get_upgrade_data(mock_session_factory, 123, 456, "trading")

        assert "error" in data
        assert "fully upgraded" in data["error"]

    def test_get_upgrade_data_none_target(self, mock_session_factory):
        """Test get_upgrade_data with None target defaults to trading."""
        with (
            patch("services.shop_service.User.get_trading_hall_level", return_value=1),
            patch("services.shop_service.User.get_emeralds", return_value=200),
        ):
            data = self.service.get_upgrade_data(mock_session_factory, 123, 456, target=None)

        assert "type" in data or "error" in data

    def test_get_user_emeralds_zero(self, mock_session_factory):
        """Test getting emerald count when user has zero."""
        with patch("services.shop_service.User.get_emeralds", return_value=0):
            emeralds = self.service.get_user_emeralds(mock_session_factory, 123, 456)

        assert emeralds == 0

    def test_get_user_emeralds_none(self, mock_session_factory):
        """Test getting emerald count when user has no entry."""
        with patch("services.shop_service.User.get_emeralds", return_value=None):
            emeralds = self.service.get_user_emeralds(mock_session_factory, 123, 456)

        assert emeralds == 0
