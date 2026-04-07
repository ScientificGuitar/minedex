"""Tests for TradeService."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.trade_service import TradeService


class TestTradeService:
    """Test suite for TradeService."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_service(self, mock_mobs, mock_villagers, mock_items, request):
        """Set up service once per class using request fixture."""
        request.cls.service = TradeService(mock_mobs, mock_villagers, mock_items)

    def test_can_trade_with_farmer_success(self, mock_session_factory):
        """Test successful farmer trade check."""
        with (
            patch("services.trade_service.UserDB.get_user") as mock_user,
            patch("services.trade_service.CollectionDB.get_mob_count") as mock_count,
        ):
            mock_user_obj = MagicMock()
            mock_user_obj.trading_hall_level = 1
            mock_user.return_value = mock_user_obj
            mock_count.return_value = 5

            result = self.service.can_trade_with_farmer(mock_session_factory, 123, 456, "zombie", 3)

        assert result["can_trade"] is True
        assert result["mob"]["name"] == "Zombie"

    def test_can_trade_with_farmer_no_duplicates(self, mock_session_factory):
        """Test farmer trade with no duplicate mobs."""
        with (
            patch("services.trade_service.UserDB.get_user") as mock_user,
            patch("services.trade_service.CollectionDB.get_mob_count") as mock_count,
        ):
            mock_user_obj = MagicMock()
            mock_user_obj.trading_hall_level = 1
            mock_user.return_value = mock_user_obj
            mock_count.return_value = 1

            result = self.service.can_trade_with_farmer(mock_session_factory, 123, 456, "zombie", 1)

        assert result["can_trade"] is False
        assert "duplicate" in result["error"]

    def test_can_trade_with_farmer_no_level(self, mock_session_factory):
        """Test farmer trade when farmer not unlocked."""
        with patch("services.trade_service.UserDB.get_user") as mock_user:
            mock_user_obj = MagicMock()
            mock_user_obj.trading_hall_level = 0
            mock_user.return_value = mock_user_obj

            result = self.service.can_trade_with_farmer(mock_session_factory, 123, 456, "zombie", 1)

        assert result["can_trade"] is False
        assert "Farmer" in result["error"]

    def test_calculate_farmer_trade(self, mock_mobs):
        """Test calculating farmer trade reward."""
        result = self.service.calculate_farmer_trade(mock_mobs["zombie"], 3)

        assert result["mob_amount"] == 3
        assert result["emeralds"] > 0

    def test_perform_farmer_trade(self, mock_session_factory):
        """Test performing farmer trade."""
        with (
            patch("services.trade_service.CollectionDB.remove_mob"),
            patch("services.trade_service.UserDB.add_emeralds"),
        ):
            result = self.service.perform_farmer_trade(mock_session_factory, 123, 456, "zombie", 3, 30)

        assert result["success"] is True

    def test_can_trade_with_cleric_success(self, mock_session_factory):
        """Test successful cleric trade check."""
        with (
            patch("services.trade_service.UserDB.get_user") as mock_user,
            patch("services.trade_service.CollectionDB.get_mob_count") as mock_count,
        ):
            mock_user_obj = MagicMock()
            mock_user_obj.trading_hall_level = 2
            mock_user.return_value = mock_user_obj
            mock_count.return_value = 6

            result = self.service.can_trade_with_cleric(mock_session_factory, 123, 456, "zombie", 4)

        assert result["can_trade"] is True

    def test_can_trade_with_cleric_odd_amount(self, mock_session_factory):
        """Test cleric trade with odd number of mobs."""
        with (
            patch("services.trade_service.UserDB.get_user") as mock_user,
            patch("services.trade_service.CollectionDB.get_mob_count") as mock_count,
        ):
            mock_user_obj = MagicMock()
            mock_user_obj.trading_hall_level = 2
            mock_user.return_value = mock_user_obj
            mock_count.return_value = 6

            result = self.service.can_trade_with_cleric(mock_session_factory, 123, 456, "zombie", 3)

        assert result["can_trade"] is False
        assert "pairs" in result["error"]

    def test_calculate_cleric_trade(self, mock_mobs):
        """Test calculating cleric trade reward."""
        result = self.service.calculate_cleric_trade(mock_mobs["zombie"], 4)

        assert result["mob_amount"] == 4
        assert result["token_count"] == 2

    def test_perform_cleric_trade(self, mock_session_factory):
        """Test performing cleric trade."""
        with (
            patch("services.trade_service.CollectionDB.remove_mob"),
            patch("services.trade_service.InventoryDB.add_to_inventory"),
        ):
            result = self.service.perform_cleric_trade(mock_session_factory, 123, 456, "zombie", 4, "uncommon", 2)

        assert result["success"] is True

    def test_can_trade_with_farmer_amount_exceeds_count(self, mock_session_factory):
        """Test farmer trade when amount exceeds available mobs."""
        user = SimpleNamespace(trading_hall_level=1)
        with (
            patch("services.trade_service.UserDB.get_user", return_value=user),
            patch("services.trade_service.CollectionDB.get_mob_count", return_value=3),
        ):
            result = self.service.can_trade_with_farmer(mock_session_factory, 123, 456, "zombie", 5)

        assert result["can_trade"] is False
        assert "at least" in result["error"] or "up to" in result["error"]

    def test_can_trade_with_cleric_nonexistent_mob(self, mock_session_factory):
        """Test cleric trade with non-existent mob."""
        user = SimpleNamespace(trading_hall_level=2)
        with patch("services.trade_service.UserDB.get_user", return_value=user):
            result = self.service.can_trade_with_cleric(mock_session_factory, 123, 456, "nonexistent_mob", 4)

        assert result["can_trade"] is False
        assert "does not exist" in result["error"]

    def test_can_trade_with_cleric_amount_exceeds_count(self, mock_session_factory):
        """Test cleric trade when amount exceeds available mobs."""
        user = SimpleNamespace(trading_hall_level=2)
        with (
            patch("services.trade_service.UserDB.get_user", return_value=user),
            patch("services.trade_service.CollectionDB.get_mob_count", return_value=3),
        ):
            result = self.service.can_trade_with_cleric(mock_session_factory, 123, 456, "zombie", 4)

        assert result["can_trade"] is False
        assert "at least 1 copy" in result["error"]

    def test_can_trade_with_cleric_exact_minimum(self, mock_session_factory):
        """Test cleric trade with exact minimum duplicates (needs 3+ total)."""
        user = SimpleNamespace(trading_hall_level=2)
        with (
            patch("services.trade_service.UserDB.get_user", return_value=user),
            patch("services.trade_service.CollectionDB.get_mob_count", return_value=5),
        ):
            result = self.service.can_trade_with_cleric(mock_session_factory, 123, 456, "zombie", 2)

        assert result["can_trade"] is True
        assert result["mob"]["name"] == "Zombie"

    def test_calculate_farmer_trade_reward(self, mock_mobs):
        """Test farmer trade calculates correct reward."""
        result = self.service.calculate_farmer_trade(mock_mobs["zombie"], 1)

        assert result["mob_amount"] == 1
        assert result["emeralds"] > 0

    def test_perform_farmer_trade_success(self, mock_session_factory):
        """Test successful farmer trade execution."""
        with (
            patch("services.trade_service.CollectionDB.remove_mob") as mock_remove,
            patch("services.trade_service.UserDB.add_emeralds") as mock_reward,
        ):
            result = self.service.perform_farmer_trade(mock_session_factory, 123, 456, "zombie", 2, 20)

        assert result["success"] is True
        assert mock_remove.called
        assert mock_reward.called
