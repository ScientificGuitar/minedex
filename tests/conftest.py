"""Test configuration and fixtures."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def mock_mobs():
    """Load actual mobs from mobs.json."""
    data_dir = Path(__file__).parent.parent / "src" / "data"
    with open(data_dir / "mobs.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mock_items():
    """Load actual items from items.json."""
    data_dir = Path(__file__).parent.parent / "src" / "data"
    with open(data_dir / "items.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mock_mobs_by_rarity(mock_mobs):
    """Group mobs by rarity from actual data."""
    by_rarity = {
        "Legendary": [],
        "Epic": [],
        "Rare": [],
        "Uncommon": [],
        "Common": [],
    }
    for mob_id, mob_data in mock_mobs.items():
        rarity = mob_data.get("rarity", "Common")
        if rarity in by_rarity:
            by_rarity[rarity].append(mob_id)
    return by_rarity


@pytest.fixture(scope="session")
def mock_villagers():
    """Fixture for mock villager data with all required fields."""
    return {
        "farmer": {
            "name": "Farmer",
            "level": 1,
            "price": 100,
            "description": "Trades mobs for emeralds",
            "commands": [],
        },
        "cleric": {"name": "Cleric", "level": 2, "price": 200, "description": "Trades mobs for tokens", "commands": []},
        "librarian": {"name": "Librarian", "level": 3, "price": 300, "description": "Focus roll", "commands": []},
        "toolsmith": {"name": "Toolsmith", "level": 4, "price": 400, "description": "Reroll", "commands": []},
    }


@pytest.fixture
def mock_session_factory():
    """Fixture for mock database session factory."""
    return MagicMock()


def create_mock_user(
    trading_hall_level=0,
    last_claim_at=None,
    last_reroll_at=None,
    last_daily_at=None,
    last_roll_at=None,
    timezone=None,
    balance=1000,
):
    """Factory for creating mock user objects with sensible defaults."""
    return SimpleNamespace(
        trading_hall_level=trading_hall_level,
        last_claim_at=last_claim_at,
        last_reroll_at=last_reroll_at,
        last_daily_at=last_daily_at,
        last_roll_at=last_roll_at,
        timezone=timezone,
        balance=balance,
    )


@pytest.fixture
def mock_user_factory():
    """Fixture providing a factory for mock users."""
    return create_mock_user
