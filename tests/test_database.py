"""Tests for database layer operations through service interactions."""

import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from database.achievement import AchievementDB
from database.collection import Collection
from database.inventory import Inventory
from database.user import User


@pytest.fixture
def mock_session_factory():
    """Create a mock session factory that returns a mock session."""
    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = None
    mock_factory = MagicMock(return_value=mock_session)
    return mock_factory


class TestUserDatabaseOperations:
    """Tests for User database CRUD operations."""

    def test_get_user_exists(self, mock_session_factory):
        """Test retrieving an existing user."""
        user_model = SimpleNamespace(guild_id=123, user_id=456, emeralds=100, unlocked_villagers="farmer")
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        with patch("database.user.UserModel") as mock_user_model:
            result = User.get_user(mock_session_factory, 123, 456)

        assert result is not None

    def test_get_user_not_exists(self, mock_session_factory):
        """Test retrieving a non-existent user."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None

        result = User.get_user(mock_session_factory, 999, 999)

        assert result is None

    def test_ensure_user_creates_new_user(self, mock_session_factory):
        """Test that ensure_user creates a user if not exists."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        # First query for user, second for stats
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [None, None]

        with patch("database.user.UserModel"), patch("database.user.StatsModel"):
            User.ensure_user(mock_session_factory, 123, 456)

        # Should add user and stats
        assert mock_session.add.call_count >= 2
        assert mock_session.commit.called

    def test_has_focus_rolled_today_false(self, mock_session_factory):
        """Test focus roll check when user hasn't rolled today."""
        user_model = SimpleNamespace(last_focus_roll_at=None)
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        now_ts = int(time.time())
        result = User.has_focus_rolled_today(mock_session_factory, 123, 456, now_ts)

        assert result is False

    def test_record_focus_roll(self, mock_session_factory):
        """Test recording a focus roll."""
        user_model = SimpleNamespace(last_focus_roll_at=None)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        now_ts = int(time.time())
        User.record_focus_roll(mock_session_factory, 123, 456, now_ts)

        assert user_model.last_focus_roll_at == now_ts
        assert mock_session.commit.called

    def test_get_unlocked_villagers(self, mock_session_factory):
        """Test getting unlocked villagers."""
        user_model = SimpleNamespace(unlocked_villagers="farmer,cleric")
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        result = User.get_unlocked_villagers(mock_session_factory, 123, 456)

        assert result == ["farmer", "cleric"]

    def test_unlock_villager(self, mock_session_factory):
        """Test unlocking a villager."""
        user_model = SimpleNamespace(unlocked_villagers="farmer", trading_hall_level=1)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.unlock_villager(mock_session_factory, 123, 456, "cleric")

        assert "cleric" in user_model.unlocked_villagers
        assert mock_session.commit.called

    def test_is_villager_unlocked(self, mock_session_factory):
        """Test checking if a villager is unlocked."""
        user_model = SimpleNamespace(unlocked_villagers="farmer")
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        assert User.is_villager_unlocked(mock_session_factory, 123, 456, "farmer") is True
        assert User.is_villager_unlocked(mock_session_factory, 123, 456, "cleric") is False

    def test_update_last_daily_at(self, mock_session_factory):
        """Test updating last daily claim timestamp."""
        user_model = SimpleNamespace(last_daily_at=0)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        now_ts = int(time.time())
        User.update_last_daily_at(mock_session_factory, 123, 456, now_ts)

        assert user_model.last_daily_at == now_ts
        assert mock_session.commit.called

    def test_record_roll(self, mock_session_factory):
        """Test recording a roll action."""
        user_model = SimpleNamespace(last_roll_at=None)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        now_ts = int(time.time())
        User.record_roll(mock_session_factory, 123, 456, now_ts)

        assert user_model.last_roll_at == now_ts
        assert mock_session.commit.called

    def test_record_reroll(self, mock_session_factory):
        """Test recording a reroll action."""
        user_model = SimpleNamespace(last_reroll_at=None)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        now_ts = int(time.time())
        User.record_reroll(mock_session_factory, 123, 456, now_ts)

        assert user_model.last_reroll_at == now_ts
        assert mock_session.commit.called

    def test_has_focus_rolled_today_true(self, mock_session_factory):
        """Test focus roll check when user has rolled today."""
        now_ts = int(time.time())
        user_model = SimpleNamespace(last_focus_roll_at=now_ts)
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        with patch("database.user.is_same_game_day", return_value=True):
            result = User.has_focus_rolled_today(mock_session_factory, 123, 456, now_ts)

        assert result is True

    def test_add_emeralds(self, mock_session_factory):
        """Test adding emeralds to user balance."""
        user_model = SimpleNamespace(emeralds=100)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.add_emeralds(mock_session_factory, 123, 456, 50)

        assert user_model.emeralds == 150
        assert mock_session.commit.called

    def test_get_emeralds(self, mock_session_factory):
        """Test getting user emeralds balance."""
        user_model = SimpleNamespace(emeralds=250)
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        result = User.get_emeralds(mock_session_factory, 123, 456)

        assert result == 250

    def test_ensure_stats(self, mock_session_factory):
        """Test ensure_stats creates stats if not exists."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("database.user.StatsModel"):
            User.ensure_stats(mock_session_factory, 123, 456)

        assert mock_session.add.called
        assert mock_session.commit.called

    def test_get_stats(self, mock_session_factory):
        """Test retrieving user stats."""
        stats_model = SimpleNamespace(total_rolls=10)
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = stats_model

        result = User.get_stats(mock_session_factory, 123, 456)

        assert result.total_rolls == 10


class TestCollectionDatabaseOperations:
    """Tests for Collection database CRUD operations."""

    def test_get_collection_with_mobs(self, mock_session_factory):
        """Test retrieving a user's collection."""
        # get_collection queries (CollectionModel.mob_id, CollectionModel.amount) and returns tuples
        mobs = [("zombie", 2), ("creeper", 1)]
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.all.return_value = mobs

        result = Collection.get_collection(mock_session_factory, 123, 456)

        assert result is not None
        assert len(result) == 2
        assert result[0]["mob_id"] == "zombie"
        assert result[0]["amount"] == 2

    def test_add_to_collection_new_mob(self, mock_session_factory):
        """Test adding new mob to collection."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("database.collection.CollectionModel"):
            Collection.add_to_collection(mock_session_factory, 123, 456, "zombie")

        assert mock_session.add.called
        assert mock_session.commit.called


class TestInventoryDatabaseOperations:
    """Tests for Inventory database CRUD operations."""

    def test_add_to_inventory_new_item(self, mock_session_factory):
        """Test adding new item to inventory."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("database.inventory.InventoryModel"):
            Inventory.add_to_inventory(mock_session_factory, 123, 456, "token_uncommon", 2)

        assert mock_session.add.called
        assert mock_session.commit.called


class TestAchievementDatabaseOperations:
    """Tests for Achievement database CRUD operations."""

    def test_unlock_achievement_new(self, mock_session_factory):
        """Test unlocking a new achievement."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        # Mock that achievement doesn't exist yet
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("database.achievement.AchievementUnlockModel") as mock_achievement_model:
            AchievementDB.unlock_achievement(mock_session_factory, 123, 456, "first_mob", 1000000000)

        assert mock_session.add.called
        assert mock_session.commit.called


class TestAdditionalUserDatabaseOperations:
    """Additional tests for User database operations (stat tracking)."""

    def test_increment_total_rolls(self, mock_session_factory):
        """Test incrementing total rolls counter."""
        stats_model = SimpleNamespace(total_rolls=5)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        # Side effect: first ensure_stats query, then increment query
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [stats_model, stats_model]

        User.increment_total_rolls(mock_session_factory, 123, 456)

        assert stats_model.total_rolls == 6
        assert mock_session.commit.called

    def test_increment_total_claims(self, mock_session_factory):
        """Test incrementing total claims counter."""
        stats_model = SimpleNamespace(total_claims=10)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [stats_model, stats_model]

        User.increment_total_claims(mock_session_factory, 123, 456)

        assert stats_model.total_claims == 11
        assert mock_session.commit.called

    def test_add_emeralds_gained(self, mock_session_factory):
        """Test adding to total emeralds gained."""
        stats_model = SimpleNamespace(total_emeralds_gained=100)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [stats_model, stats_model]

        User.add_emeralds_gained(mock_session_factory, 123, 456, 50)

        assert stats_model.total_emeralds_gained == 150
        assert mock_session.commit.called

    def test_add_mobs_traded(self, mock_session_factory):
        """Test adding to total mobs traded."""
        stats_model = SimpleNamespace(total_mobs_traded=25)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [stats_model, stats_model]

        User.add_mobs_traded(mock_session_factory, 123, 456, 3)

        assert stats_model.total_mobs_traded == 28
        assert mock_session.commit.called
