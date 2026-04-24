"""Test configuration and fixtures."""

import json
import sys
from collections import defaultdict
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


@pytest.fixture(scope="session")
def mock_shop_data():
    """Fixture for mock shop data."""
    return {
        "permanent_upgrades": {
            "farmer": {
                "name": "Farmer",
                "description": "Trades mobs for emeralds",
                "price": 100,
                "type": "villager_unlock",
                "requirements": []
            },
            "cleric": {
                "name": "Cleric",
                "description": "Trades mobs for tokens",
                "price": 200,
                "type": "villager_unlock",
                "requirements": ["farmer"]
            }
        },
        "consumables": {
            "token": {
                "name": "Token",
                "description": "Single-use token",
                "price": 50,
                "type": "token",
                "item_id": "rare"
            }
        }
    }


@pytest.fixture
def mock_session_factory():
    """Fixture for mock database session factory."""
    return MagicMock()


def create_mock_user(
    trading_hall_level=0,
    unlocked_villagers="",
    last_claim_at=None,
    last_reroll_at=None,
    last_daily_at=None,
    last_roll_at=None,
    emeralds=1000,
):
    """Factory for creating mock user objects with sensible defaults."""
    return SimpleNamespace(
        trading_hall_level=trading_hall_level,
        unlocked_villagers=unlocked_villagers,
        last_claim_at=last_claim_at,
        last_reroll_at=last_reroll_at,
        last_daily_at=last_daily_at,
        last_roll_at=last_roll_at,
        emeralds=emeralds,
    )


def create_mock_user_snapshot(
    emeralds=0,
    trading_hall_level=0,
    total_rolls=0,
    total_claims=0,
    total_farmer_trades=0,
    total_cleric_trades=0,
    total_emeralds_gained=0,
    total_unique=0,
    mobs_by_rarity=None,
    mobs_by_tag=None,
    unique_mobs=None,
):
    if mobs_by_rarity is None:
        mobs_by_rarity = defaultdict(set)

    if mobs_by_tag is None:
        mobs_by_tag = defaultdict(set)

    if unique_mobs is None:
        unique_mobs = set()

    return SimpleNamespace(
        emeralds=emeralds,
        trading_hall_level=trading_hall_level,
        total_rolls=total_rolls,
        total_claims=total_claims,
        total_farmer_trades=total_farmer_trades,
        total_cleric_trades=total_cleric_trades,
        total_trades=total_farmer_trades + total_cleric_trades,
        total_emeralds_gained=total_emeralds_gained,
        total_unique=total_unique,
        mobs_by_rarity=mobs_by_rarity,
        mobs_by_tag=mobs_by_tag,
        unique_mobs=unique_mobs,
    )


@pytest.fixture
def mock_user_factory():
    """Fixture providing a factory for mock users."""
    return create_mock_user


@pytest.fixture
def mock_user_snapshot_factory():
    """Fixture providing a factory for mock users."""
    return create_mock_user_snapshot
