"""Tests for RaidService."""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
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
            patch.object(self.service, "get_active_raid", return_value=None)
        ):
            # Sum of emeralds is 500 (threshold is 1000)
            mock_session.query.return_value.filter_by.return_value.all.return_value = [(200,), (300,)]
            
            result = self.service.check_spawn_trigger(mock_session_factory, 123)
            assert result is False

    def test_check_spawn_trigger_true(self, mock_session_factory):
        """Test raid trigger when guild wealth meets threshold."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        
        with (
            patch.object(self.service, "get_active_raid", return_value=None),
            patch.object(self.service, "spawn_raid")
        ):
            # Sum is 1500 (threshold 1000)
            mock_session.query.return_value.filter_by.return_value.all.return_value = [(1000,), (500,)]
            
            result = self.service.check_spawn_trigger(mock_session_factory, 123)
            assert result is True

    def test_spawn_raid(self, mock_session_factory):
        """Test spawning a new raid boss."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        
        # Mock player count for power calculation
        mock_session.query.return_value.filter_by.return_value.count.return_value = 2
        
        raid = self.service.spawn_raid(mock_session_factory, 123, boss_id="wither")
        
        assert raid.boss_id == "wither"
        assert raid.current_phase == 1
        assert raid.target_power == 100 # 2 players * 50 multiplier
        assert raid.is_active is True

    def test_donate_mob_valid_tag(self, mock_session_factory):
        """Test donating a mob with the correct tag (Phase 1)."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        # Mock active raid
        raid = MagicMock(boss_id="wither", current_phase=1, target_tag="undead", target_power=100, current_power=0)
        contribution = MagicMock(mobs_donated_this_phase=0, total_power_donated=0)
        
        # Skeleton has 'undead' tag and rarity 'Common'
        mob_id = "skeleton"
        
        with (
            patch.object(self.service, "get_active_raid", return_value=raid),
            patch("database.collection.Collection.get_mob_count", return_value=5),
            patch.object(self.service, "_ensure_contribution_entry", return_value=contribution),
            patch("database.collection.Collection.remove_mob")
        ):
            # Side effects for sequential queries
            mock_session.query.return_value.filter_by.return_value.first.side_effect = [raid, contribution]
            
            result = self.service.donate_mob(mock_session_factory, 123, 456, mob_id, 1)
            
            assert result["success"] is True
            assert result["mob_name"] == "Skeleton"
            assert result["power_donated"] > 0

    def test_donate_mob_invalid_rarity(self, mock_session_factory):
        """Test donating a mob that doesn't meet phase rarity requirements (Phase 3)."""
        raid = MagicMock(boss_id="wither", current_phase=3, target_power=200, current_power=0)
        
        # Skeleton is 'Common', Phase 3 requires 'Epic' or 'Legendary'
        mob_id = "skeleton"
        
        with (
            patch.object(self.service, "get_active_raid", return_value=raid),
            patch("database.collection.Collection.get_mob_count", return_value=5),
            patch.object(self.service, "_ensure_contribution_entry", return_value=MagicMock())
        ):
            result = self.service.donate_mob(mock_session_factory, 123, 456, mob_id, 1)
            
            assert result["success"] is False
            assert "high-tier" in result["error"]

    def test_calculate_rewards(self, mock_session_factory):
        """Test reward calculation for raid contributors."""
        mock_session = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        # Guild 123 has 100 total power donated
        cont1 = MagicMock(user_id=111, total_power_donated=60, is_claimed=False) # Top 1 (60%)
        cont2 = MagicMock(user_id=222, total_power_donated=30, is_claimed=False) # Top 2 (30%)
        cont3 = MagicMock(user_id=333, total_power_donated=10, is_claimed=False) # Top 3 (10%)
        
        mock_session.query.return_value.filter_by.return_value.all.return_value = [cont1, cont2, cont3]
        
        with (
            patch("database.user.User.add_emeralds"),
            patch("database.inventory.Inventory.add_to_inventory")
        ):
            rewards = self.service.calculate_rewards(mock_session_factory, 123)
            
            assert len(rewards) == 3
            # Top 1 with >10% should be Diamond
            assert rewards[0]["user_id"] == 111
            assert rewards[0]["tier"] == "diamond"
            # Top 3 with exactly 10% should be Diamond
            assert rewards[2]["user_id"] == 333
            assert rewards[2]["tier"] == "diamond"
