"""Tests for RollService."""

import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from constants import RARITY_WEIGHTS
from services.roll_service import RollService


class TestRollService:
    """Test suite for RollService."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_service(self, mock_mobs, mock_mobs_by_rarity, mock_villagers, request):
        """Set up service once per class using request fixture."""
        request.cls.service = RollService(mock_mobs, mock_mobs_by_rarity, mock_villagers)

    def test_roll_rarity_standard(self):
        """Test rolling rarity with standard settings."""
        rarity = RollService.roll_rarity()
        assert rarity in RARITY_WEIGHTS.keys()

    def test_roll_rarity_excluded(self):
        """Test rolling rarity with exclusion."""
        for _ in range(10):
            rarity = RollService.roll_rarity(exclude={"Common"})
            assert rarity != "Common"

    def test_roll_rarity_allowed(self):
        """Test rolling rarity with allowed set."""
        for _ in range(10):
            rarity = RollService.roll_rarity(allowed={"Common"})
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
        user = mock_user_factory(trading_hall_level=4, last_reroll_at=None)
        with patch("services.roll_service.UserDB.get_user", return_value=user):
            result = self.service.can_reroll(mock_session_factory, 123, 456, int(time.time()))

        assert result["can_reroll"] is True

    def test_can_reroll_already_claimed_today(self, mock_session_factory, mock_user_factory):
        """Test reroll check when user already claimed today."""
        now = int(time.time())
        user = mock_user_factory(trading_hall_level=4, last_claim_at=now - 3600)  # Claimed 1 hour ago (same day)
        with patch("services.roll_service.UserDB.get_user", return_value=user):
            result = self.service.can_reroll(mock_session_factory, 123, 456, now)

        assert result["can_reroll"] is False
        assert "already claimed" in result["error"]

    def test_can_reroll_already_rerolled_today(self, mock_session_factory, mock_user_factory):
        """Test reroll check when user already rerolled today."""
        now = int(time.time())
        user = mock_user_factory(trading_hall_level=4, last_reroll_at=now - 3600)  # Rerolled 1 hour ago (same day)
        with patch("services.roll_service.UserDB.get_user", return_value=user):
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
        user = mock_user_factory(last_claim_at=now - 3600, last_roll_at=now - 7200)  # Claimed 1 hour ago (same day)
        with patch("services.roll_service.UserDB.get_user", return_value=user):
            result = self.service.can_roll(mock_session_factory, 123, 456, now)

        assert result["can_roll"] is False
        assert "already claimed" in result["error"]

    def test_can_roll_focus_already_done_today(self, mock_session_factory, mock_user_factory):
        """Test can_roll with focus mode when already done today."""
        now = int(time.time())
        user = mock_user_factory(trading_hall_level=3, last_claim_at=now - 86400, last_roll_at=now - 7200)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.has_focus_rolled_today", return_value=True),
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
            patch("services.roll_service.UserDB.record_roll"),
        ):
            mob_id, mob = self.service.perform_roll(mock_session_factory, 123, 456, now)

        assert mob_id in self.service.mobs
        assert mob == self.service.mobs[mob_id]

    def test_perform_reroll(self, mock_session_factory):
        """Test performing a reroll."""
        now = int(time.time())
        with patch("services.roll_service.UserDB.record_reroll"):
            mob_id, mob = self.service.perform_reroll(mock_session_factory, 123, 456, now)

        assert mob_id in self.service.mobs
        assert mob == self.service.mobs[mob_id]

    def test_claim_mob(self, mock_session_factory):
        """Test claiming a mob and receiving rewards."""
        mob_id = list(self.service.mobs.keys())[0]
        mob = self.service.mobs[mob_id]
        now = int(time.time())

        with (
            patch("services.roll_service.CollectionDB.add_to_collection"),
            patch("services.roll_service.UserDB.update_last_claim_at"),
            patch("services.roll_service.UserDB.add_emeralds") as mock_add_emeralds,
        ):
            reward = self.service.claim_mob(mock_session_factory, 123, 456, mob_id, mob, now)

        assert reward > 0
        assert isinstance(reward, int)
        mock_add_emeralds.assert_called_once()

    def test_can_roll_focus_mode(self, mock_session_factory, mock_user_factory):
        """Test can_roll with focus mode (requires librarian)."""
        now = int(time.time())
        user = mock_user_factory(trading_hall_level=3, last_claim_at=now - 86400, last_roll_at=now - 7200)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.has_focus_rolled_today", return_value=False),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="focus")

        assert result["can_roll"] is True
        assert result["mode"] == "focus"

    def test_can_roll_focus_mode_no_librarian(self, mock_session_factory, mock_user_factory):
        """Test can_roll with focus mode when librarian not unlocked."""
        now = int(time.time())
        user = mock_user_factory(trading_hall_level=2)
        with patch("services.roll_service.UserDB.get_user", return_value=user):
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
            patch("services.roll_service.InventoryDB.get_item", return_value=inventory_item),
        ):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="token", value="uncommon")

        assert result["can_roll"] is True
        assert result["mode"] == "token"
        assert result["value"] == "uncommon"

    def test_can_roll_token_mode_no_rarity(self, mock_session_factory, mock_user_factory):
        """Test can_roll with token mode but no rarity specified."""
        now = int(time.time())
        user = mock_user_factory()
        with patch("services.roll_service.UserDB.get_user", return_value=user):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="token")

        assert result["can_roll"] is False
        assert "specify a token" in result["error"]

    def test_can_roll_token_mode_invalid_rarity(self, mock_session_factory, mock_user_factory):
        """Test can_roll with token mode but invalid rarity."""
        now = int(time.time())
        user = mock_user_factory()
        with patch("services.roll_service.UserDB.get_user", return_value=user):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="token", value="invalid_rarity")

        assert result["can_roll"] is False
        assert "Invalid token rarity" in result["error"]

    def test_can_roll_invalid_mode(self, mock_session_factory, mock_user_factory):
        """Test can_roll with invalid mode."""
        now = int(time.time())
        user = mock_user_factory()
        with patch("services.roll_service.UserDB.get_user", return_value=user):
            result = self.service.can_roll(mock_session_factory, 123, 456, now, mode="invalid_mode")

        assert result["can_roll"] is False
        assert "Invalid roll type" in result["error"]

    def test_perform_roll_focus_excludes_common(self, mock_session_factory, mock_user_factory):
        """Test perform_roll with focus mode excludes common rarities."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 86400, last_roll_at=now - 7200)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.UserDB.record_focus_roll"),
        ):
            mob_id, mob = self.service.perform_roll(mock_session_factory, 123, 456, now, mode="focus")

        assert mob["rarity"] != "Common"

    def test_perform_roll_token_consumes_item(self, mock_session_factory, mock_user_factory):
        """Test perform_roll with token mode consumes the token."""
        now = int(time.time())
        user = mock_user_factory(last_claim_at=now - 86400, last_roll_at=now - 7200)
        inventory_item = SimpleNamespace(amount=2)
        with (
            patch("services.roll_service.UserDB.get_user", return_value=user),
            patch("services.roll_service.InventoryDB.get_item", return_value=inventory_item),
            patch("services.roll_service.InventoryDB.add_to_inventory") as mock_consume,
            patch("services.roll_service.UserDB.record_roll"),
        ):
            mob_id, mob = self.service.perform_roll(mock_session_factory, 123, 456, now, mode="token", value="rare")

        mock_consume.assert_called_once_with(mock_session_factory, 123, 456, "rare", -1)
        assert mob["rarity"] == "Rare"

    def test_can_reroll_no_toolsmith(self, mock_mobs, mock_mobs_by_rarity, mock_villagers, mock_session_factory):
        """Test reroll check when toolsmith not available."""
        service = RollService(mock_mobs, mock_mobs_by_rarity, mock_villagers)

        with patch("services.roll_service.UserDB.get_user") as mock_user:
            mock_user_obj = MagicMock()
            mock_user_obj.trading_hall_level = 1
            mock_user.return_value = mock_user_obj

            result = service.can_reroll(mock_session_factory, 123, 456, 1000)

        assert result["can_reroll"] is False
        assert "Toolsmith" in result["error"]

    def test_roll_random_mob(self, mock_mobs, mock_mobs_by_rarity, mock_villagers):
        """Test rolling a random mob."""
        service = RollService(mock_mobs, mock_mobs_by_rarity, mock_villagers)

        mob_id, mob = service.roll_random_mob()

        assert mob_id in mock_mobs
        assert mob == mock_mobs[mob_id]

    def test_build_mob_embed_data(self, mock_mobs, mock_mobs_by_rarity, mock_villagers, mock_session_factory):
        service = RollService(mock_mobs, mock_mobs_by_rarity, mock_villagers)

        with patch("services.roll_service.CollectionDB.get_mob_count") as mock_count:
            mock_count.return_value = 2

            data = service.build_mob_embed_data(mock_session_factory, 123, 456, "slime", mock_mobs["slime"])

        assert data["owned_amount"] == 2
        assert data["rerolled"] is False

    def test_can_roll_on_cooldown(self, mock_mobs, mock_mobs_by_rarity, mock_villagers):
        service = RollService(mock_mobs, mock_mobs_by_rarity, mock_villagers)

        now = int(time.time())
        mock_user = SimpleNamespace(
            last_claim_at=0,
            timezone=None,
            last_roll_at=now - 60,
            trading_hall_level=0,
        )

        with patch("services.roll_service.UserDB.get_user", return_value=mock_user):
            result = service.can_roll(MagicMock(), 123, 456, now)

        assert result["can_roll"] is False
        assert "roll again" in result["error"]

    def test_perform_roll(self, mock_mobs, mock_mobs_by_rarity, mock_villagers):
        service = RollService(mock_mobs, mock_mobs_by_rarity, mock_villagers)

        rolled_mob = {
            "id": "zombie",
            "name": "Zombie",
            "rarity": "Common",
        }

        now = int(time.time())

        with (
            patch("services.roll_service.UserDB.record_roll") as mock_record_roll,
            patch(
                "services.roll_service.RollService.roll_random_mob",
                return_value=("zombie", rolled_mob),
            ),
        ):
            mob_id, mob = service.perform_roll(None, 123, 456, now)

        assert mob_id == "zombie"
        assert mob["id"] == "zombie"
        assert mob["name"] == "Zombie"
        assert mob["rarity"] == "Common"
        mock_record_roll.assert_called_once_with(None, 123, 456, now)

        def test_claim_mob(self):
            # Mock session factory and database calls
            mock_session = Mock()

            with patch("services.roll_service.CollectionDB.add_mob") as mock_add_mob:
                result = self.service.claim_mob(Mock(return_value=mock_session), 123, 456, "zombie")

                self.assertTrue(result["success"])
                self.assertEqual(result["mob"]["id"], "zombie")

                # Verify mob was added to collection
                mock_add_mob.assert_called_once_with(mock_session, 456, "zombie")


if __name__ == "__main__":
    unittest.main()
