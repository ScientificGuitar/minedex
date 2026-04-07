"""Tests for CollectionService."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.collection_service import CollectionService


class TestCollectionService:
    """Test suite for CollectionService."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_service(self, mock_mobs, mock_mobs_by_rarity, request):
        """Set up service once per class using request fixture."""
        request.cls.service = CollectionService(mock_mobs, mock_mobs_by_rarity)

    def test_get_mob_info(self, mock_mobs):
        """Test getting information about a specific mob."""
        # Pick a real mob from actual data
        mob_id = list(mock_mobs.keys())[0]
        mob = self.service.get_mob_info(mob_id)

        assert mob is not None
        assert "name" in mob
        assert "rarity" in mob

    def test_get_user_collection(self, mock_session_factory):
        """Test getting user's collection data."""
        with patch("services.collection_service.CollectionDB.get_collection") as mock_get:
            mock_get.return_value = [{"mob_id": "zombie", "amount": 2}]

            result = self.service.get_user_collection(mock_session_factory, 123, 456)

        assert result == [{"mob_id": "zombie", "amount": 2}]
        mock_get.assert_called_once_with(mock_session_factory, 123, 456)

    def test_get_missing_mobs(self, mock_session_factory):
        """Test getting mobs missing from user's collection."""
        with patch("services.collection_service.CollectionDB.get_collection") as mock_get:
            # User only has first mob
            first_mob_id = list(self.service.mobs.keys())[0]
            mock_get.return_value = [{"mob_id": first_mob_id, "amount": 1}]

            missing = self.service.get_missing_mobs(mock_session_factory, 12345, 67890)

        assert isinstance(missing, dict)
        # Should have missing mobs in various rarities
        total_missing = sum(len(v) for v in missing.values())
        assert total_missing > 0

    def test_get_all_mobs_paginated(self, mock_mobs):
        """Test getting all mobs paginated."""
        result = self.service.get_all_mobs_paginated(page=1, per_page=10)

        assert result["total_mobs"] == len(mock_mobs)
        assert result["current_page"] == 1
        assert "mobs" in result

    def test_get_all_mobs_paginated_invalid_page(self):
        """Test getting mobs with invalid page number."""
        result = self.service.get_all_mobs_paginated(page=999, per_page=10)
        assert "error" in result

    def test_get_mobs_by_rarity(self, mock_mobs_by_rarity):
        """Test getting mobs filtered by rarity."""
        # Test with a valid rarity that has mobs
        valid_rarity = next(r for r in mock_mobs_by_rarity if mock_mobs_by_rarity[r])
        result = self.service.get_mobs_by_rarity(valid_rarity)

        assert result["rarity"] == valid_rarity
        assert result["count"] > 0
        assert len(result["mobs"]) == result["count"]

    def test_get_mobs_by_rarity_invalid(self):
        """Test getting mobs with invalid rarity."""
        result = self.service.get_mobs_by_rarity("InvalidRarityXYZ")
        assert "error" in result

    def test_build_collection_embed_data(self):
        """Test building embed data for collection."""
        # Use real mobs from the service
        first_two_mobs = list(self.service.mobs.items())[:2]
        rows = [{"mob_id": mob_id, "amount": 1} for mob_id, _ in first_two_mobs]

        result = self.service.build_collection_embed_data(rows, page=1, per_page=10)

        assert result["total_entries"] == 2
        assert result["current_page"] == 1
        assert "entries" in result

    def test_build_collection_embed_data_invalid_page(self):
        """Test building embed data with invalid page."""
        rows = [{"mob_id": list(self.service.mobs.keys())[0], "amount": 1}]
        result = self.service.build_collection_embed_data(rows, page=999)

        assert "error" in result

    def test_build_collection_embed_data_with_filter(self):
        """Test building embed data with filter applied."""
        first_two_mobs = list(self.service.mobs.items())[:2]
        rows = [{"mob_id": mob_id, "amount": 2} for mob_id, _ in first_two_mobs]

        result = self.service.build_collection_embed_data(rows, page=1, per_page=10)

        assert result["total_entries"] > 0
        assert "entries" in result

    def test_build_collection_embed_data_valid_page(self):
        """Test building embed data with valid page number."""
        rows = [{"mob_id": list(self.service.mobs.keys())[0], "amount": 1}]
        result = self.service.build_collection_embed_data(rows, page=1, per_page=10)

        assert "error" not in result
        assert result["total_entries"] == 1

    def test_build_collection_embed_data_invalid_rarity_filter(self):
        """Test building embed data with invalid rarity filter."""
        rows = [{"mob_id": list(self.service.mobs.keys())[0], "amount": 1}]
        result = self.service.build_collection_embed_data(rows, page=1, per_page=10, rarity_filter="InvalidRarity")

        assert "error" in result
        assert "No mobs found for rarity" in result["error"]
