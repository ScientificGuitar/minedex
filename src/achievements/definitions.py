"""
Achievement definitions

Each achievement is defined as a dictionary with the following keys:
- id: Unique identifier for the achievement
- name: Display name
- description: Description of the achievement
- category: Category for grouping (e.g., "collection", "trading", "exploration")
- triggers: List of trigger types that should evaluate this achievement
- hidden: Whether the achievement is hidden until unlocked
- check: Function that takes a player snapshot and returns True if achieved
"""

from dataclasses import dataclass
from typing import Any, Callable, List


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    category: str
    triggers: List[str]
    hidden: bool
    check: Callable[[Any], bool]


def create_achievement(
    id: str,
    name: str,
    description: str,
    category: str,
    triggers: List[str],
    hidden: bool = False,
) -> Achievement:
    """Helper to create achievement definitions."""
    return Achievement(
        id=id,
        name=name,
        description=description,
        category=category,
        triggers=triggers,
        hidden=hidden,
        check=lambda snapshot: False,  # Will be set later
    )


# Achievement definitions
ACHIEVEMENTS = [
    # Collection achievements
    create_achievement(
        id="first_mob",
        name="First Steps",
        description="Collect your first mob",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="unique_10",
        name="Collector",
        description="Collect 10 unique mobs",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="unique_25",
        name="Dedicated Collector",
        description="Collect 25 unique mobs",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="unique_50",
        name="Master Collector",
        description="Collect 50 unique mobs",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="unique_100",
        name="Elite Collector",
        description="Collect 100 unique mobs",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="first_legendary",
        name="Legendary Hunter",
        description="Collect your first Legendary mob",
        category="collection",
        triggers=["claim"],
    ),
    # Rarity completion achievements
    create_achievement(
        id="complete_common",
        name="Common Conqueror",
        description="Collect all Common mobs",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="complete_uncommon",
        name="Uncommon Conqueror",
        description="Collect all Uncommon mobs",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="complete_rare",
        name="Rare Conqueror",
        description="Collect all Rare mobs",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="complete_epic",
        name="Epic Conqueror",
        description="Collect all Epic mobs",
        category="collection",
        triggers=["claim"],
    ),
    create_achievement(
        id="complete_legendary",
        name="Legendary Conqueror",
        description="Collect all Legendary mobs",
        category="collection",
        triggers=["claim"],
    ),
    # World completion achievements
    create_achievement(
        id="complete_overworld",
        name="Overworld Explorer",
        description="Collect all Overworld mobs",
        category="exploration",
        triggers=["claim"],
    ),
    create_achievement(
        id="complete_nether",
        name="Nether Explorer",
        description="Collect all Nether mobs",
        category="exploration",
        triggers=["claim"],
    ),
    create_achievement(
        id="complete_end",
        name="End Explorer",
        description="Collect all End mobs",
        category="exploration",
        triggers=["claim"],
    ),
    # Boss hunter
    create_achievement(
        id="boss_hunter",
        name="Boss Hunter",
        description="Collect the Ender Dragon and Wither",
        category="exploration",
        triggers=["claim"],
    ),
    # Full collection
    create_achievement(
        id="full_collection",
        name="Master of Mobs",
        description="Collect every mob in the game",
        category="collection",
        triggers=["claim"],
    ),
    # Trading achievements
    create_achievement(
        id="first_trade",
        name="Merchant",
        description="Complete your first trade",
        category="trading",
        triggers=["farmer_trade", "cleric_trade"],
    ),
    # Economy achievements
    create_achievement(
        id="emerald_1000",
        name="Wealthy",
        description="Accumulate 1,000 emeralds",
        category="economy",
        triggers=["claim", "farmer_trade"],
    ),
    create_achievement(
        id="emerald_10000",
        name="Rich",
        description="Accumulate 10,000 emeralds",
        category="economy",
        triggers=["claim", "farmer_trade"],
    ),
    # Lifetime statistics achievements
    create_achievement(
        id="roller_10",
        name="Rolling Stone",
        description="Roll 10 times",
        category="lifetime",
        triggers=["claim"],
    ),
    create_achievement(
        id="roller_100",
        name="Serial Roller",
        description="Roll 100 times",
        category="lifetime",
        triggers=["claim"],
    ),
    create_achievement(
        id="roller_1000",
        name="Unstoppable Roller",
        description="Roll 1,000 times",
        category="lifetime",
        triggers=["claim"],
    ),
    create_achievement(
        id="claimer_50",
        name="Claim Master",
        description="Claim 50 mobs",
        category="lifetime",
        triggers=["claim"],
    ),
    create_achievement(
        id="claimer_250",
        name="Prolific Claimer",
        description="Claim 250 mobs",
        category="lifetime",
        triggers=["claim"],
    ),
    create_achievement(
        id="trader_5",
        name="Trader",
        description="Complete 5 trades",
        category="lifetime",
        triggers=["farmer_trade", "cleric_trade"],
    ),
    create_achievement(
        id="trader_50",
        name="Master Trader",
        description="Complete 50 trades",
        category="lifetime",
        triggers=["farmer_trade", "cleric_trade"],
    ),
    create_achievement(
        id="trader_100",
        name="Black Market",
        description="Trade away 100 mobs",
        category="lifetime",
        triggers=["farmer_trade", "cleric_trade"],
    ),
    create_achievement(
        id="trader_1000",
        name="Mob Liquidator",
        description="Trade away 1,000 mobs",
        category="lifetime",
        triggers=["farmer_trade", "cleric_trade"],
    ),
    create_achievement(
        id="emeralds_earned_5000",
        name="Merchant",
        description="Earn 5,000 emeralds from all sources",
        category="lifetime",
        triggers=["claim", "farmer_trade"],
    ),
    create_achievement(
        id="emeralds_earned_50000",
        name="Tycoon",
        description="Earn 50,000 emeralds from all sources",
        category="lifetime",
        triggers=["claim", "farmer_trade"],
    ),
]


# Achievement lookup by ID
ACHIEVEMENT_BY_ID = {achievement.id: achievement for achievement in ACHIEVEMENTS}


def get_achievement(achievement_id: str) -> Achievement | None:
    """Get an achievement by ID."""
    return ACHIEVEMENT_BY_ID.get(achievement_id)


def get_achievements_by_trigger(trigger: str) -> List[Achievement]:
    """Get all achievements that should be evaluated for a given trigger."""
    return [achievement for achievement in ACHIEVEMENTS if trigger in achievement.triggers]
