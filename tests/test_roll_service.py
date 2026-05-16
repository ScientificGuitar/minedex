"""Tests for RollService."""

import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from constants import RARITY_WEIGHTS
from services.roll_service import RollService


class TestRollService:
    """Test suite for RollService."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_service(self, mock_mobs, mock_mobs_by_rarity, mock_villagers, mock_items, request):
        """Set up service once per class using request fixture."""
        request.cls.service = RollService(mock_mobs, mock_mobs_by_rarity, mock_villagers, mock_items)

    def test_roll_rarity_standard(self):
        """Test rolling rarity with standard settings."""
        rarity = self.service.roll_rarity()
        assert rarity in RARITY_WEIGHTS.keys()

    def test_roll_rarity_excluded(self):
        """Test rolling rarity with exclusion."""
        for _ in range(10):
            rarity = self.service.roll_rarity(exclude={"Common"})
            assert rarity != "Common"

    def test_roll_rarity_allowed(self):
        """Test rolling rarity with allowed set."""
        for _ in range(10):
            rarity = self.service.roll_rarity(allowed={"Common"})
            assert rarity == "Common"

    def test_get_cooldown_remaining_no_last_action(self):
        """Test cooldown calculation with no previous action."""
        remaining = RollService.get_cooldown_remaining(None, 1000, 3600)
        assert remaining == 0

    def test_get_cooldown_remaining_within_cooldown(self):
        """Test cooldown calculation within cooldown period."""
        remaining = RollService.get_cooldown_remaining(100, 1000, 3600)
        assert remaining == 2700

    def test_get_cooldown_remaining_past_cooldown(self):
        """Test cooldown calculation after cooldown expires."""
        remaining = RollService.get_cooldown_remaining(100, 5000, 3600)
        assert remaining == 0

    def test_can_reroll_success(self, mock_session_factory, mock_user_factory):
        """Test successful reroll check."""
        user = mock_user_factory(last_reroll_at=None)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.is_villager_unlocked", return_value=True),
            patch("services.roll_service.is_same_game_day", return_value=False),
        ):
            result = self.service.can_reroll(mock_session_factory, 123, 456, int(time.time()))

        assert result["can_reroll"] is True

    def test_can_reroll_already_claimed_today(self, mock_session_factory, mock_user_factory):
        """Test reroll check when user already claimed today."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 3600)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.is_villager_unlocked", return_value=True),
            patch("services.roll_service.is_same_game_day", side_effect=[True, False]),
        ):
            result = self.service.can_reroll(mock_session_factory, 123, 456, now)

        assert result["can_reroll"] is False
        assert "already claimed" in result["error"]

    def test_can_reroll_already_rerolled_today(self, mock_session_factory, mock_user_factory):
        """Test reroll check when user already rerolled today."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 3600)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.is_villager_unlocked", return_value=True),
            patch("services.roll_service.is_same_game_day", side_effect=[False, True]),
        ):
            result = self.service.can_reroll(mock_session_factory, 123, 456, now)

        assert result["can_reroll"] is False
        assert "already rerolled" in result["error"]

    def test_roll_random_mob(self, mock_mobs):
        """Test rolling a random mob."""
        mob_id, mob = self.service.roll_random_mob()

        assert mob_id in mock_mobs
        assert mob == mock_mobs[mob_id]

    def test_can_roll_already_claimed_today(self, mock_session_factory, mock_user_factory):
        """Test can_roll when user already claimed today."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 3600, last_roll_at=now - 7200)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("strategies.standard.is_same_game_day", return_value=True),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now)

        assert result["can_roll"] is False
        assert "already claimed" in result["error"]

    def test_can_roll_focus_already_done_today(self, mock_session_factory, mock_user_factory):
        """Test can_roll with focus mode when already done today."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 86400, last_roll_at=now - 7200)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.is_villager_unlocked", return_value=True),
            patch("strategies.focus.is_same_game_day", return_value=False),
            patch("database.user.User.has_focus_rolled_today", return_value=True),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="focus")

        assert result["can_roll"] is False
        assert "already focus rolled" in result["error"]

    def test_perform_roll(self, mock_session_factory, mock_user_factory):
        """Test performing a roll."""
        now = int(time.time())
        user = mock_user_factory(last_roll_at=None, last_claim_at=None)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("database.user.User.record_roll"),
            patch("database.user.User.increment_total_rolls"),
        ):
            mob_id, mob = self.service.perform_roll(mock_session_factory, 123, 456, now)

        assert mob_id in self.service.mobs
        assert mob == self.service.mobs[mob_id]

    def test_perform_reroll(self, mock_session_factory):
        """Test performing a reroll."""
        now = int(time.time())
        with patch("database.user.User.record_reroll"):
            mob_id, mob = self.service.perform_reroll(mock_session_factory, 123, 456, now)

        assert mob_id in self.service.mobs
        assert mob == self.service.mobs[mob_id]

    def test_claim_mob(self, mock_session_factory):
        """Test claiming a mob and receiving rewards."""
        mob_id = list(self.service.mobs.keys())[0]
        mob = self.service.mobs[mob_id]
        now = int(time.time())

        with (
            patch("database.collection.Collection.add_to_collection"),
            patch("database.user.User.update_last_claim_at"),
            patch("database.user.User.add_emeralds") as mock_add_emeralds,
            patch("database.user.User.increment_total_claims"),
            patch("database.user.User.add_emeralds_gained"),
        ):
            reward = self.service.claim_mob(mock_session_factory, 123, 456, mob_id, mob, now)

        assert reward >= 0
        assert isinstance(reward, int)
        mock_add_emeralds.assert_called_once()

    def test_can_roll_focus_mode(self, mock_session_factory, mock_user_factory):
        """Test can_roll with focus mode (requires librarian)."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 86400, last_roll_at=now - 7200)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.is_villager_unlocked", return_value=True),
            patch("strategies.focus.is_same_game_day", return_value=False),
            patch("database.user.User.has_focus_rolled_today", return_value=False),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="focus")

        assert result["can_roll"] is True
        assert result["mode"] == "focus"

    def test_focus_roll_does_not_affect_standard_roll_cooldown(self, mock_session_factory, mock_user_factory):
        """Test that focus roll does not block standard roll cooldown."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 86400, last_roll_at=None)

        with (
            patch("database.user.User.record_focus_roll"),
            patch("database.user.User.increment_total_rolls"),
        ):
            self.service.perform_roll(mock_session_factory, 123, 456, now, mode="focus")

        # Standard roll should still be allowed since last_roll_at was not updated
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("strategies.standard.is_same_game_day", return_value=False),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now)

        assert result["can_roll"] is True

    def test_can_roll_focus_mode_no_librarian(self, mock_session_factory, mock_user_factory):
        """Test can_roll with focus mode when librarian not unlocked."""
        now = int(time.time())
        user = mock_user_factory()
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.is_villager_unlocked", return_value=False),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="focus")

        assert result["can_roll"] is False
        assert "Librarian" in result["error"]

    def test_can_roll_token_mode_valid(self, mock_session_factory, mock_user_factory):
        """Test can_roll with token mode and valid token."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 86400, last_roll_at=now - 7200)
        inventory_item = SimpleNamespace(amount=1)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("strategies.token.is_same_game_day", return_value=False),
            patch("database.inventory.Inventory.get_item", return_value=inventory_item),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="token", value="uncommon")

        assert result["can_roll"] is True
        assert result["mode"] == "token"
        assert result["value"] == "uncommon"

    def test_can_reroll_no_toolsmith(self, mock_session_factory, mock_user_factory):
        """Test reroll check when toolsmith not available."""
        user = mock_user_factory()
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.is_villager_unlocked", return_value=False),
        ):
            result = self.service.can_reroll(mock_session_factory, 123, 456, 1000)

        assert result["can_reroll"] is False
        assert "Toolsmith" in result["error"]

    def test_can_roll_on_cooldown(self, mock_session_factory, mock_user_factory):
        """Test can_roll when on cooldown."""
        now = int(time.time())
        user = mock_user_factory(last_roll_at=now - 60, last_claim_at=now - 86400)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("strategies.standard.is_same_game_day", return_value=False),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now)

        assert result["can_roll"] is False
        assert "roll again" in result["error"]
