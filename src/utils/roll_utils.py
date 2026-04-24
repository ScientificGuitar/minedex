import random
from typing import Dict, Optional, Tuple
from constants import RARITY_WEIGHTS


def roll_rarity(exclude: Optional[set] = None, allowed: Optional[set] = None) -> str:
    """Roll a rarity based on weights."""
    exclude = exclude or set()
    if allowed:
        rarities = [r for r in allowed if r in RARITY_WEIGHTS]
    else:
        rarities = [r for r in RARITY_WEIGHTS if r not in exclude]
    
    if not rarities:
        # Fallback to all if everything is excluded (shouldn't happen with correct config)
        rarities = list(RARITY_WEIGHTS.keys())
        
    weights = [RARITY_WEIGHTS[r] for r in rarities]
    return random.choices(rarities, weights=weights, k=1)[0]


def roll_random_mob(mobs: Dict[str, Dict], mobs_by_rarity: Dict[str, list[str]], exclude: Optional[set] = None, allowed: Optional[set] = None) -> Tuple[str, Dict]:
    """Roll a random mob based on rarity weights."""
    rarity = roll_rarity(exclude, allowed)
    
    # Ensure rarity has mobs
    if not mobs_by_rarity.get(rarity):
        # Fallback to Common if requested rarity is empty
        rarity = "Common"
        
    mob_id = random.choice(mobs_by_rarity[rarity])
    return mob_id, mobs[mob_id]
