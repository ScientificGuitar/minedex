import json
import os

MOBS_FILE = "src/data/mobs.json"
BALANCING_FILE = "src/data/balancing.json"

def complete_centralization():
    if not os.path.exists(MOBS_FILE) or not os.path.exists(BALANCING_FILE):
        print("Error: Files not found.")
        return

    with open(BALANCING_FILE, "r") as f:
        balancing = json.load(f)

    with open(MOBS_FILE, "r") as f:
        mobs = json.load(f)

    emerald_rewards = balancing["emerald_rewards"]
    farmer_values = balancing["farmer_values"]
    cleric_tokens = balancing["cleric_tokens"]

    for mob_id, mob in mobs.items():
        rarity = mob.get("rarity", "Common")
        
        # Add per-mob economy stats based on rarity defaults
        mob["claim_reward"] = emerald_rewards.get(rarity, 0)
        mob["farmer_value"] = farmer_values.get(rarity, 0)
        mob["token_reward"] = cleric_tokens.get(rarity, None)

    with open(MOBS_FILE, "w") as f:
        json.dump(mobs, f, indent=2)
    
    print(f"Centralized economy data into {len(mobs)} mobs.")

if __name__ == "__main__":
    complete_centralization()
