"""Tests for RaidService."""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.raid_service import RaidService


class TestRaidService:
    """Test suite for RaidService."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_service(self, mock_mobs, mock_bosses, mock_items, mock_artifacts, request):
        """Set up service once per class using request fixture."""
        request.cls.service = RaidService(mock_mobs, mock_bosses, mock_items, mock_artifacts)

    def test_check_spawn_trigger_false(self, mock_session_factory):
        """Test raid trigger when guild wealth is below threshold."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        with (
            patch.object(self.service, "get_active_raid", return_value=None),
            patch.object(self.service, "get_last_raid_end", return_value=None)
        ):
            mock_session.query.return_value.filter_by.return_value.all.return_value = [(200,), (300,)]

            result = self.service.check_spawn_trigger(mock_session_factory, 123)
            assert result is False

    def test_check_spawn_trigger_true(self, mock_session_factory):
        """Test raid trigger when guild wealth meets threshold."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        with (
            patch.object(self.service, "get_active_raid", return_value=None),
            patch.object(self.service, "get_last_raid_end", return_value=None),
            patch.object(self.service, "spawn_raid")
        ):
            mock_session.query.return_value.filter_by.return_value.all.return_value = [(1000,), (500,)]

            result = self.service.check_spawn_trigger(mock_session_factory, 123)
            assert result is True

    def test_spawn_raid(self, mock_session_factory):
        """Test spawning a new raid boss."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter_by.return_value.count.return_value = 2

        raid = self.service.spawn_raid(mock_session_factory, 123, boss_id="wither")

        assert raid.boss_id == "wither"
        assert raid.current_phase == 1
        assert raid.target_power == 100
        assert raid.is_active is True

    def test_spawn_raid_with_channel_id(self, mock_session_factory):
        """Test spawning a raid with a start channel."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.count.return_value = 2

        raid = self.service.spawn_raid(mock_session_factory, 123, boss_id="wither", channel_id=456)

        assert raid.start_channel_id == 456

    def test_donate_mob_valid_tag(self, mock_session_factory):
        """Test donating a mob with the correct tag (Phase 1)."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        raid = MagicMock(boss_id="wither", current_phase=1, target_tag="undead", target_power=100, current_power=0, spawned_at=1000)
        contribution = MagicMock(mobs_donated_this_phase=0, total_power_donated=0)

        mob_id = "skeleton"

        with (
            patch("database.collection.Collection.get_mob_count", return_value=5),
            patch.object(self.service, "_ensure_contribution_entry", return_value=contribution),
            patch("database.collection.Collection.remove_mob")
        ):
            mock_session.query.return_value.filter_by.return_value.first.return_value = raid

            result = self.service.donate_mob(mock_session_factory, 123, 456, mob_id, 1)

            assert result["success"] is True
            assert result["mob_name"] == "Skeleton"
            assert result["power_donated"] > 0

    def test_donate_mob_invalid_rarity(self, mock_session_factory):
        """Test donating a mob that doesn't meet phase rarity requirements (Phase 3)."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        raid = MagicMock(boss_id="wither", current_phase=3, target_power=200, current_power=0, spawned_at=1000)

        mob_id = "skeleton"

        with (
            patch.object(self.service, "get_active_raid", return_value=raid),
            patch("database.collection.Collection.get_mob_count", return_value=5),
            patch.object(self.service, "_ensure_contribution_entry", return_value=MagicMock())
        ):
            result = self.service.donate_mob(mock_session_factory, 123, 456, mob_id, 1)

            assert result["success"] is False
            assert "high-tier" in result["error"]

    def test_calculate_rewards_success(self, mock_session_factory):
        """Test reward calculation for a completed raid."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        raid = MagicMock(spawned_at=1000, ended_at=2000, is_active=False, current_phase=3)
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = raid

        cont1 = MagicMock(user_id=111, total_power_donated=60, is_claimed=False)
        cont2 = MagicMock(user_id=222, total_power_donated=30, is_claimed=False)
        cont3 = MagicMock(user_id=333, total_power_donated=10, is_claimed=False)

        mock_session.query.return_value.filter_by.return_value.all.return_value = [cont1, cont2, cont3]

        with (
            patch("database.user.User.add_emeralds"),
            patch("database.inventory.Inventory.add_to_inventory")
        ):
            rewards = self.service.calculate_rewards(mock_session_factory, 123)

            assert len(rewards) == 3
            assert rewards[0]["user_id"] == 111
            assert rewards[0]["tier"] == "diamond"
            assert rewards[2]["user_id"] == 333
            assert rewards[2]["tier"] == "diamond"

    def test_calculate_rewards_failure_phase1(self, mock_session_factory):
        """Test that no rewards are given when raid fails before completing Phase 1."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        raid = MagicMock(spawned_at=1000, ended_at=2000, is_active=False, current_phase=1)
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = raid

        cont1 = MagicMock(user_id=111, total_power_donated=60, is_claimed=False)
        cont2 = MagicMock(user_id=222, total_power_donated=30, is_claimed=False)

        mock_session.query.return_value.filter_by.return_value.all.return_value = [cont1, cont2]

        rewards = self.service.calculate_rewards(mock_session_factory, 123)

        assert len(rewards) == 0
        assert cont1.is_claimed is True
        assert cont2.is_claimed is True

    def test_check_spawn_trigger_passes_channel_id(self, mock_session_factory):
        """Test that check_spawn_trigger passes channel_id to spawn_raid."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        with (
            patch.object(self.service, "get_active_raid", return_value=None),
            patch.object(self.service, "get_last_raid_end", return_value=None),
            patch.object(self.service, "spawn_raid") as mock_spawn
        ):
            mock_session.query.return_value.filter_by.return_value.all.return_value = [(2000,)]

            result = self.service.check_spawn_trigger(mock_session_factory, 123, channel_id=789)

            assert result is True
            mock_spawn.assert_called_once_with(mock_session_factory, 123, channel_id=789)
