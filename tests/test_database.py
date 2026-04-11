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
        user_model = SimpleNamespace(guild_id=123, user_id=456, emeralds=100, trading_hall_level=1)
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
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("database.user.UserModel") as mock_user_model:
            User.ensure_user(mock_session_factory, 123, 456)

        assert mock_session.add.called
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

    def test_upgrade_trading_hall(self, mock_session_factory):
        """Test upgrading trading hall level."""
        user_model = SimpleNamespace(trading_hall_level=2)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.upgrade_trading_hall(mock_session_factory, 123, 456)

        assert user_model.trading_hall_level == 3
        assert mock_session.commit.called

    def test_get_timezone(self, mock_session_factory):
        """Test getting user timezone."""
        user_model = SimpleNamespace(timezone="America/New_York")
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        result = User.get_timezone(mock_session_factory, 123, 456)

        assert result == "America/New_York"

    def test_set_timezone(self, mock_session_factory):
        """Test setting user timezone."""
        user_model = SimpleNamespace(timezone="UTC")
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.set_timezone(mock_session_factory, 123, 456, "Europe/London")

        assert user_model.timezone == "Europe/London"
        assert mock_session.commit.called

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
        earlier_ts = now_ts - 3600  # 1 hour ago
        user_model = SimpleNamespace(last_focus_roll_at=earlier_ts, timezone="UTC")
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        with patch("database.user.same_utc_day", return_value=True):
            result = User.has_focus_rolled_today(mock_session_factory, 123, 456, now_ts)

        assert result is True

    def test_has_focus_rolled_today_user_not_found(self, mock_session_factory):
        """Test focus roll check when user doesn't exist."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None

        now_ts = int(time.time())
        result = User.has_focus_rolled_today(mock_session_factory, 123, 456, now_ts)

        assert result is False

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

    def test_get_emeralds_user_not_found(self, mock_session_factory):
        """Test getting emeralds when user doesn't exist."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None

        result = User.get_emeralds(mock_session_factory, 123, 456)

        assert result is None

    def test_get_trading_hall_level(self, mock_session_factory):
        """Test getting trading hall level."""
        user_model = SimpleNamespace(trading_hall_level=3)
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = user_model

        result = User.get_trading_hall_level(mock_session_factory, 123, 456)

        assert result == 3

    def test_get_trading_hall_level_user_not_found(self, mock_session_factory):
        """Test getting trading hall level when user doesn't exist."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None

        result = User.get_trading_hall_level(mock_session_factory, 123, 456)

        assert result is None

    def test_upgrade_trading_hall_user_not_found(self, mock_session_factory):
        """Test upgrading trading hall when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.upgrade_trading_hall(mock_session_factory, 123, 456)

        assert not mock_session.commit.called

    def test_record_roll_user_not_found(self, mock_session_factory):
        """Test recording roll when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.record_roll(mock_session_factory, 123, 456, int(time.time()))

        assert not mock_session.commit.called

    def test_record_reroll_user_not_found(self, mock_session_factory):
        """Test recording reroll when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.record_reroll(mock_session_factory, 123, 456, int(time.time()))

        assert not mock_session.commit.called

    def test_record_focus_roll_user_not_found(self, mock_session_factory):
        """Test recording focus roll when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.record_focus_roll(mock_session_factory, 123, 456, int(time.time()))

        assert not mock_session.commit.called

    def test_update_last_claim_at_user_not_found(self, mock_session_factory):
        """Test updating last claim when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.update_last_claim_at(mock_session_factory, 123, 456, int(time.time()))

        assert not mock_session.commit.called

    def test_update_last_daily_at_user_not_found(self, mock_session_factory):
        """Test updating last daily when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.update_last_daily_at(mock_session_factory, 123, 456, int(time.time()))

        assert not mock_session.commit.called

    def test_add_emeralds_user_not_found(self, mock_session_factory):
        """Test adding emeralds when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.add_emeralds(mock_session_factory, 123, 456, 50)

        assert not mock_session.commit.called

    def test_set_timezone_user_not_found(self, mock_session_factory):
        """Test setting timezone when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.set_timezone(mock_session_factory, 123, 456, "America/New_York")

        assert not mock_session.commit.called

    def test_get_timezone_user_not_found(self, mock_session_factory):
        """Test getting timezone when user doesn't exist."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None

        result = User.get_timezone(mock_session_factory, 123, 456)

        assert result is None


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

    def test_get_collection_empty(self, mock_session_factory):
        """Test retrieving empty collection."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.all.return_value = []

        result = Collection.get_collection(mock_session_factory, 123, 456)

        assert result == []

    def test_add_to_collection_new_mob(self, mock_session_factory):
        """Test adding new mob to collection."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("database.collection.CollectionModel"):
            Collection.add_to_collection(mock_session_factory, 123, 456, "zombie")

        assert mock_session.add.called
        assert mock_session.commit.called

    def test_add_to_collection_existing_mob(self, mock_session_factory):
        """Test incrementing existing mob in collection."""
        existing_mob = SimpleNamespace(amount=2)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_mob

        Collection.add_to_collection(mock_session_factory, 123, 456, "zombie")

        assert existing_mob.amount == 3
        assert mock_session.commit.called

    def test_get_mob_count(self, mock_session_factory):
        """Test getting count of specific mob."""
        collection = SimpleNamespace(amount=5)
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = collection

        result = Collection.get_mob_count(mock_session_factory, 123, 456, "zombie")

        assert result == 5

    def test_get_mob_count_not_owned(self, mock_session_factory):
        """Test getting count when mob not owned."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None

        result = Collection.get_mob_count(mock_session_factory, 123, 456, "zombie")

        assert result is None


class TestInventoryDatabaseOperations:
    """Tests for Inventory database CRUD operations."""

    def test_get_items(self, mock_session_factory):
        """Test retrieving all items in inventory."""
        items = [
            SimpleNamespace(item_id="token_uncommon", amount=2),
            SimpleNamespace(item_id="token_rare", amount=1),
        ]
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.all.return_value = items

        result = Inventory.get_items(mock_session_factory, 123, 456)

        assert result is not None
        assert len(result) == 2

    def test_get_items_empty(self, mock_session_factory):
        """Test retrieving empty inventory."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.all.return_value = []

        result = Inventory.get_items(mock_session_factory, 123, 456)

        assert result == []

    def test_get_item(self, mock_session_factory):
        """Test getting specific item from inventory."""
        item = SimpleNamespace(item_id="token_uncommon", amount=5)
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = item

        result = Inventory.get_item(mock_session_factory, 123, 456, "token_uncommon")

        assert result is not None
        assert result.amount == 5

    def test_get_item_not_exists(self, mock_session_factory):
        """Test getting item that doesn't exist."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None

        result = Inventory.get_item(mock_session_factory, 123, 456, "nonexistent")

        assert result is None

    def test_add_to_inventory_new_item(self, mock_session_factory):
        """Test adding new item to inventory."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("database.inventory.InventoryModel"):
            Inventory.add_to_inventory(mock_session_factory, 123, 456, "token_uncommon", 2)

        assert mock_session.add.called
        assert mock_session.commit.called

    def test_add_to_inventory_existing_item(self, mock_session_factory):
        """Test incrementing existing item in inventory."""
        existing_item = SimpleNamespace(amount=3)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_item

        Inventory.add_to_inventory(mock_session_factory, 123, 456, "token_uncommon", 2)

        assert existing_item.amount == 5
        assert mock_session.commit.called


class TestAchievementDatabaseOperations:
    """Tests for Achievement database CRUD operations."""

    def test_get_user_achievements_with_data(self, mock_session_factory):
        """Test getting user achievements when they exist."""
        # Mock achievement unlock objects
        unlock1 = SimpleNamespace(achievement_id="first_mob", unlocked_at=1000000000)
        unlock2 = SimpleNamespace(achievement_id="unique_10", unlocked_at=1000000001)
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [
            unlock1,
            unlock2,
        ]

        result = AchievementDB.get_user_achievements(mock_session_factory, 123, 456)

        assert len(result) == 2
        assert result[0]["achievement_id"] == "first_mob"
        assert result[0]["unlocked_at"] == 1000000000
        assert result[1]["achievement_id"] == "unique_10"
        assert result[1]["unlocked_at"] == 1000000001

    def test_get_user_achievements_empty(self, mock_session_factory):
        """Test getting user achievements when none exist."""
        mock_session_factory.return_value.__enter__.return_value.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []

        result = AchievementDB.get_user_achievements(mock_session_factory, 123, 456)

        assert result == []

    def test_unlock_achievement_new(self, mock_session_factory):
        """Test unlocking a new achievement."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        # Mock that achievement doesn't exist yet
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("database.achievement.AchievementUnlockModel") as mock_achievement_model:
            AchievementDB.unlock_achievement(mock_session_factory, 123, 456, "first_mob", 1000000000)

        assert mock_session.add.called
        assert mock_session.commit.called
        # Verify the model was created with correct parameters
        mock_achievement_model.assert_called_once_with(
            guild_id=123, user_id=456, achievement_id="first_mob", unlocked_at=1000000000
        )

    def test_unlock_achievement_already_exists(self, mock_session_factory):
        """Test unlocking an achievement that already exists (should not add again)."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        # Mock that achievement already exists
        mock_session.query.return_value.filter_by.return_value.first.return_value = SimpleNamespace()

        AchievementDB.unlock_achievement(mock_session_factory, 123, 456, "first_mob", 1000000000)

        # Should not add or commit since it already exists
        assert not mock_session.add.called
        assert not mock_session.commit.called


class TestAdditionalUserDatabaseOperations:
    """Additional tests for User database operations (stat tracking)."""

    def test_increment_total_rolls(self, mock_session_factory):
        """Test incrementing total rolls counter."""
        user_model = SimpleNamespace(total_rolls=5)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.increment_total_rolls(mock_session_factory, 123, 456)

        assert user_model.total_rolls == 6
        assert mock_session.commit.called

    def test_increment_total_rolls_user_not_found(self, mock_session_factory):
        """Test incrementing total rolls when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.increment_total_rolls(mock_session_factory, 123, 456)

        assert not mock_session.commit.called

    def test_increment_total_claims(self, mock_session_factory):
        """Test incrementing total claims counter."""
        user_model = SimpleNamespace(total_claims=10)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.increment_total_claims(mock_session_factory, 123, 456)

        assert user_model.total_claims == 11
        assert mock_session.commit.called

    def test_increment_total_claims_user_not_found(self, mock_session_factory):
        """Test incrementing total claims when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.increment_total_claims(mock_session_factory, 123, 456)

        assert not mock_session.commit.called

    def test_increment_total_farmer_trades(self, mock_session_factory):
        """Test incrementing total farmer trades counter."""
        user_model = SimpleNamespace(total_farmer_trades=3)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.increment_total_farmer_trades(mock_session_factory, 123, 456)

        assert user_model.total_farmer_trades == 4
        assert mock_session.commit.called

    def test_increment_total_farmer_trades_user_not_found(self, mock_session_factory):
        """Test incrementing total farmer trades when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.increment_total_farmer_trades(mock_session_factory, 123, 456)

        assert not mock_session.commit.called

    def test_increment_total_cleric_trades(self, mock_session_factory):
        """Test incrementing total cleric trades counter."""
        user_model = SimpleNamespace(total_cleric_trades=2)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.increment_total_cleric_trades(mock_session_factory, 123, 456)

        assert user_model.total_cleric_trades == 3
        assert mock_session.commit.called

    def test_increment_total_cleric_trades_user_not_found(self, mock_session_factory):
        """Test incrementing total cleric trades when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.increment_total_cleric_trades(mock_session_factory, 123, 456)

        assert not mock_session.commit.called

    def test_add_emeralds_gained(self, mock_session_factory):
        """Test adding to total emeralds gained."""
        user_model = SimpleNamespace(total_emeralds_gained=100)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.add_emeralds_gained(mock_session_factory, 123, 456, 50)

        assert user_model.total_emeralds_gained == 150
        assert mock_session.commit.called

    def test_add_emeralds_gained_user_not_found(self, mock_session_factory):
        """Test adding emeralds gained when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.add_emeralds_gained(mock_session_factory, 123, 456, 50)

        assert not mock_session.commit.called

    def test_add_mobs_traded(self, mock_session_factory):
        """Test adding to total mobs traded."""
        user_model = SimpleNamespace(total_mobs_traded=25)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = user_model

        User.add_mobs_traded(mock_session_factory, 123, 456, 3)

        assert user_model.total_mobs_traded == 28
        assert mock_session.commit.called

    def test_add_mobs_traded_user_not_found(self, mock_session_factory):
        """Test adding mobs traded when user doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        User.add_mobs_traded(mock_session_factory, 123, 456, 3)

        assert not mock_session.commit.called


class TestAdditionalCollectionDatabaseOperations:
    """Additional tests for Collection database operations."""

    def test_remove_mob_existing(self, mock_session_factory):
        """Test removing mobs from collection when they exist."""
        collection_item = SimpleNamespace(amount=5)
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = collection_item

        Collection.remove_mob(mock_session_factory, 123, 456, "zombie", 2)

        assert collection_item.amount == 3
        assert mock_session.commit.called

    def test_remove_mob_not_found(self, mock_session_factory):
        """Test removing mobs when collection item doesn't exist."""
        mock_session = mock_session_factory.return_value.__enter__.return_value
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        Collection.remove_mob(mock_session_factory, 123, 456, "zombie", 2)

        assert not mock_session.commit.called
