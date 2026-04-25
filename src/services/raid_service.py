import random
import time
from typing import Any, Dict, List, Optional, Tuple

from database.collection import Collection as CollectionDB
from database.db import Raid as RaidModel, RaidContribution as ContributionModel, User as UserModel
from database.inventory import Inventory as InventoryDB
from database.user import User as UserDB


class RaidService:
    def __init__(self, mobs: Dict[str, Dict], bosses: Dict[str, Dict], items: Dict[str, Dict], artifacts: Dict[str, Dict] = None):
        self.mobs = mobs
        self.boss_data = bosses["bosses"]
        self.config = bosses["config"]
        self.items = items
        self.artifacts = artifacts or {}

    def calculate_rewards(self, session_factory, guild_id: int) -> List[Dict[str, Any]]:
        """Calculate and distribute rewards for the finished raid."""
        # We need the most recent raid that hasn't been claimed yet
        with session_factory() as session:
            last_raid = session.query(RaidModel).filter_by(guild_id=guild_id, is_active=False).order_by(RaidModel.ended_at.desc()).first()
            if not last_raid:
                return []

            contributions = session.query(ContributionModel).filter_by(
                guild_id=guild_id, 
                spawned_at=last_raid.spawned_at, 
                is_claimed=False
            ).all()
            
            if not contributions:
                return []

            total_server_power = sum(c.total_power_donated for c in contributions)
            if total_server_power <= 0:
                return []

            # Sort by damage to identify Top 3
            sorted_cont = sorted(contributions, key=lambda c: c.total_power_donated, reverse=True)
            
            results = []
            for idx, cont in enumerate(sorted_cont):
                user_id = cont.user_id
                power_pct = (cont.total_power_donated / total_server_power) * 100
                
                # 1. Determine Tier
                tier = "iron"
                if idx < 3 and power_pct >= 10:
                    tier = "diamond"
                elif power_pct >= 10:
                    tier = "gold"
                
                # 2. Generate Loot
                loot = self._generate_loot(tier)
                
                # 3. Distribute (Update DB)
                UserDB.add_emeralds(session_factory, guild_id, user_id, loot["emeralds"])
                for item_id, count in loot["items"].items():
                    InventoryDB.add_to_inventory(session_factory, guild_id, user_id, item_id, count)
                
                cont.is_claimed = True
                results.append({
                    "user_id": user_id,
                    "tier": tier,
                    "loot": loot,
                    "power": cont.total_power_donated
                })
            
            session.commit()
            return results

    def _generate_loot(self, tier: str) -> Dict[str, Any]:
        """Generate random loot based on crate tier."""
        loot = {"emeralds": 0, "items": {}}
        
        if tier == "diamond":
            loot["emeralds"] = random.randint(500, 1000)
            loot["items"]["epic"] = 1 # Epic token
            # 20% chance for an artifact
            if self.artifacts and random.random() < 0.20:
                art_id = random.choice(list(self.artifacts.keys()))
                loot["items"][art_id] = 1
        elif tier == "gold":
            loot["emeralds"] = random.randint(200, 450)
            loot["items"]["rare"] = 1
        else: # iron
            loot["emeralds"] = random.randint(50, 150)
            loot["items"]["uncommon"] = 1
            
        return loot

    def check_spawn_trigger(self, session_factory, guild_id: int) -> bool:
        """Check if a guild has enough total emeralds to trigger a raid."""
        # 1. Check if a raid is already active
        if self.get_active_raid(session_factory, guild_id):
            return False

        # 2. Enforce 48-hour cooldown since the last raid ended
        last_end = self.get_last_raid_end(session_factory, guild_id)
        if last_end:
            elapsed = int(time.time()) - last_end
            if elapsed < (48 * 3600): # 48 hours
                return False

        # 3. Check emerald threshold
        with session_factory() as session:
            total_emeralds = session.query(UserModel.emeralds).filter_by(guild_id=guild_id).all()
            guild_sum = sum(e[0] for e in total_emeralds)

        if guild_sum >= self.config["spawn_threshold_emeralds"]:
            self.spawn_raid(session_factory, guild_id)
            return True
        return False

    def spawn_raid(self, session_factory, guild_id: int, boss_id: Optional[str] = None) -> RaidModel:
        """Spawn a new raid boss for a guild."""
        if boss_id is None:
            boss_id = random.choice(list(self.boss_data.keys()))
        
        boss = self.boss_data[boss_id]
        first_phase = boss["phases"][0]
        
        # Determine Phase 1 tag if applicable
        target_tag = None
        if first_phase["type"] == "tag":
            target_tag = random.choice(first_phase["possible_tags"])
            
        target_power = self._calculate_target_power(session_factory, guild_id, first_phase["target_power_multiplier"])
        
        with session_factory() as session:
            new_raid = RaidModel(
                guild_id=guild_id,
                boss_id=boss_id,
                current_phase=1,
                target_tag=target_tag,
                current_power=0,
                target_power=target_power,
                spawned_at=int(time.time()),
                is_active=True
            )
            session.add(new_raid)
            session.commit()
            return new_raid

    def get_active_raid(self, session_factory, guild_id: int) -> Optional[RaidModel]:
        """Get the currently active raid for a guild."""
        with session_factory() as session:
            return session.query(RaidModel).filter_by(guild_id=guild_id, is_active=True).first()

    def get_user_contribution(self, session_factory, guild_id: int, user_id: int, spawned_at: int) -> Optional[ContributionModel]:
        """Get a user's contribution for a specific raid."""
        with session_factory() as session:
            return session.query(ContributionModel).filter_by(
                guild_id=guild_id, 
                user_id=user_id, 
                spawned_at=spawned_at
            ).first()

    def donate_mob(self, session_factory, guild_id: int, user_id: int, mob_id: str, amount: int) -> Dict[str, Any]:
        """Process a mob donation to the active raid."""
        raid = self.get_active_raid(session_factory, guild_id)
        if not raid:
            return {"success": False, "error": "There is no active raid in this village."}

        # 1. Validate Mob Ownership
        user_count = CollectionDB.get_mob_count(session_factory, guild_id, user_id, mob_id) or 0
        if user_count < amount:
            return {"success": False, "error": f"You only have {user_count} copies of this mob."}

        mob = self.mobs.get(mob_id)
        if not mob:
            return {"success": False, "error": "Invalid mob."}

        # 2. Validate Phase Requirements
        boss = self.boss_data[raid.boss_id]
        phase_config = boss["phases"][raid.current_phase - 1]
        
        if phase_config["type"] == "tag":
            if raid.target_tag not in mob.get("tags", []):
                return {"success": False, "error": f"This phase requires mobs with the **{raid.target_tag}** tag."}
        elif phase_config["type"] == "rarity_limit":
            if mob["rarity"] not in phase_config["allowed_rarities"]:
                allowed = ", ".join(phase_config["allowed_rarities"])
                return {"success": False, "error": f"This phase only accepts **{allowed}** rarities."}
        elif phase_config["type"] == "rarity_min":
            if mob["rarity"] not in phase_config["allowed_rarities"]:
                allowed = ", ".join(phase_config["allowed_rarities"])
                return {"success": False, "error": f"This phase requires high-tier energy from **{allowed}** mobs."}

        # 3. Check Individual Donation Limit
        contribution = self._ensure_contribution_entry(session_factory, guild_id, user_id, raid.spawned_at)
        if contribution.mobs_donated_this_phase + amount > self.config["player_donation_limit_per_phase"]:
            remaining = self.config["player_donation_limit_per_phase"] - contribution.mobs_donated_this_phase
            return {"success": False, "error": f"You can only donate {remaining} more mobs in this phase."}

        # 4. Process Donation
        power_donated = mob.get("base_power", 0) * amount
        CollectionDB.remove_mob(session_factory, guild_id, user_id, mob_id, amount)
        
        with session_factory() as session:
            # Update Raid Progress
            db_raid = session.query(RaidModel).filter_by(guild_id=guild_id, is_active=True).first()
            db_raid.current_power += power_donated
            
            # Update User Stats
            db_cont = session.query(ContributionModel).filter_by(
                guild_id=guild_id, 
                user_id=user_id, 
                spawned_at=raid.spawned_at
            ).first()
            db_cont.total_power_donated += power_donated
            db_cont.mobs_donated_this_phase += amount
            
            session.commit()

        # 5. Check Phase Completion
        phase_completed = False
        raid_finished = False
        if db_raid.current_power >= db_raid.target_power:
            phase_completed = True
            if db_raid.current_phase >= 3:
                raid_finished = True
                self.complete_raid(session_factory, guild_id)
            else:
                self._advance_phase(session_factory, guild_id)

        return {
            "success": True, 
            "power_donated": power_donated, 
            "phase_completed": phase_completed,
            "raid_finished": raid_finished,
            "mob_name": mob["name"]
        }

    def complete_raid(self, session_factory, guild_id: int) -> List[Dict[str, Any]]:
        """Finalize a raid and distribute rewards."""
        now = int(time.time())
        with session_factory() as session:
            raid = session.query(RaidModel).filter_by(guild_id=guild_id, is_active=True).first()
            if raid:
                raid.is_active = False
                raid.ended_at = now
                session.commit()
                
        # Trigger reward distribution
        return self.calculate_rewards(session_factory, guild_id)

    def get_last_raid_end(self, session_factory, guild_id: int) -> Optional[int]:
        """Get the timestamp when the last raid in this guild ended."""
        with session_factory() as session:
            last_raid = session.query(RaidModel).filter_by(guild_id=guild_id, is_active=False).order_by(RaidModel.ended_at.desc()).first()
            return last_raid.ended_at if last_raid else None

    def _advance_phase(self, session_factory, guild_id: int):
        """Move to the next raid phase."""
        with session_factory() as session:
            raid = session.query(RaidModel).filter_by(guild_id=guild_id, is_active=True).first()
            boss = self.boss_data[raid.boss_id]
            
            raid.current_phase += 1
            raid.current_power = 0
            
            next_phase = boss["phases"][raid.current_phase - 1]
            raid.target_power = self._calculate_target_power(session_factory, guild_id, next_phase["target_power_multiplier"])
            raid.target_tag = None # Rarity phases don't need tags
            
            # Reset player per-phase limits
            session.query(ContributionModel).filter_by(
                guild_id=guild_id, 
                spawned_at=raid.spawned_at
            ).update({
                ContributionModel.mobs_donated_this_phase: 0
            })
            
            session.commit()

    def _calculate_target_power(self, session_factory, guild_id: int, multiplier: int) -> int:
        """Calculate phase target power based on active guild population."""
        with session_factory() as session:
            player_count = session.query(UserModel).filter_by(guild_id=guild_id).count()
        
        # Base floor of 1 player to avoid division by zero or tiny bosses
        player_count = max(1, player_count)
        return player_count * multiplier

    def _ensure_contribution_entry(self, session_factory, guild_id: int, user_id: int, spawned_at: int) -> ContributionModel:
        """Ensure a user has a contribution row for the specific raid instance."""
        with session_factory() as session:
            cont = session.query(ContributionModel).filter_by(
                guild_id=guild_id, 
                user_id=user_id, 
                spawned_at=spawned_at
            ).first()
            if not cont:
                cont = ContributionModel(
                    guild_id=guild_id, 
                    user_id=user_id, 
                    spawned_at=spawned_at
                )
                session.add(cont)
                session.commit()
            return cont
