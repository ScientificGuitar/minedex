"""Tests for AchievementService."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.achievement_service import AchievementService, PlayerSnapshot


class TestAchievementService:
    """Test suite for AchievementService."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_service(self, mock_mobs, mock_mobs_by_rarity, request):
        """Set up service once per class using request fixture."""
        request.cls.service = AchievementService(mock_mobs, mock_mobs_by_rarity)

    from unittest.mock import patch

    def test_evaluate_unlocked_no_achievements(self, mock_session_factory, mock_user_snapshot_factory):
        snapshot = mock_user_snapshot_factory(
            emeralds=0,
            total_claims=0,
            total_unique=0,
        )

        with patch("services.achievement_service.PlayerSnapshot", return_value=snapshot):
            newly_unlocked = self.service.evaluate_unlocked(mock_session_factory, 123, 456, "claim", 1000000000)

        assert newly_unlocked == []

    def test_player_snapshot_creation(self, mock_session_factory, mock_mobs):
        """Test creating a player snapshot."""
        # Mock user data
        mock_user = MagicMock()
        mock_user.emeralds = 100
        mock_user.trading_hall_level = 2

        # Mock collection data
        mock_collection = [
            {"mob_id": "zombie", "amount": 1},
            {"mob_id": "skeleton", "amount": 2},
        ]

        with (
            patch("database.user.User.get_user", return_value=mock_user),
            patch("database.collection.Collection.get_collection", return_value=mock_collection),
        ):
            snapshot = PlayerSnapshot(mock_session_factory, 123, 456, mock_mobs)

            assert snapshot.emeralds == 100
            assert snapshot.trading_hall_level == 2
            assert snapshot.total_unique == 2
            assert "zombie" in snapshot.unique_mobs
            assert "skeleton" in snapshot.unique_mobs

    def test_get_user_achievements(self, mock_session_factory):
        """Test getting user achievements."""
        # Mock achievement data
        mock_achievements = [{"achievement_id": "first_mob", "unlocked_at": 1000000000}]

        with patch("database.achievement.AchievementDB.get_user_achievements", return_value=mock_achievements):
            achievements = self.service.get_user_achievements(mock_session_factory, 123, 456)

            assert len(achievements) == 1
            assert achievements[0]["id"] == "first_mob"
            assert achievements[0]["unlocked_at"] == 1000000000

    def test_get_user_stats(self, mock_session_factory, mock_mobs):
        """Test getting user statistics."""
        # Mock user data
        mock_user = MagicMock()
        mock_user.emeralds = 500
        mock_user.trading_hall_level = 3

        # Mock collection data
        mock_collection = [
            {"mob_id": "zombie", "amount": 1},
        ]

        with (
            patch("database.user.User.get_user", return_value=mock_user),
            patch("database.collection.Collection.get_collection", return_value=mock_collection),
        ):
            stats = self.service.get_user_stats(mock_session_factory, 123, 456)

            assert stats["emeralds"] == 500
            assert stats["trading_hall_level"] == 3
            assert stats["unique_mobs"] == 1
            assert stats["total_mobs"] == len(mock_mobs)
            assert stats["collection_completion"] == 1 / len(mock_mobs) * 100
