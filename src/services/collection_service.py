from collections import defaultdict
from typing import Any, Dict, List, Optional

from constants import FULL_COLLECTION_BONUS, RARITY_BUCKET_TOTALS, RARITY_COMPLETION_BONUS
from database.collection import Collection as CollectionDB
from database.db import Collection as CollectionModel
from database.db import User as UserModel


class CollectionService:
    def __init__(self, mobs: Dict[str, Dict], mobs_by_rarity: Dict[str, List[str]]):
        self.mobs = mobs
        self.mobs_by_rarity = mobs_by_rarity

    def get_user_collection(self, session_factory, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get user's collection data."""
        return CollectionDB.get_collection(session_factory, guild_id, user_id)

    def get_missing_mobs(self, session_factory, guild_id: int, user_id: int) -> Dict[str, List[str]]:
        """Get mobs missing from user's collection, grouped by rarity."""
        rows = CollectionDB.get_collection(session_factory, guild_id, user_id)
        owned_mobs = {row["mob_id"] for row in rows}
        all_mobs = set(self.mobs.keys())
        missing_mobs = all_mobs - owned_mobs

        missing_by_rarity = defaultdict(list)
        for mob_id in missing_mobs:
            mob = self.mobs[mob_id]
            missing_by_rarity[mob["rarity"]].append(mob["name"])

        return dict(missing_by_rarity)

    def get_all_mobs_paginated(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get all mobs paginated."""
        all_mobs = []
        for rarity_name, mob_ids in self.mobs_by_rarity.items():
            for mob_id in mob_ids:
                all_mobs.append((rarity_name, self.mobs[mob_id]["name"]))

        total_mobs = len(all_mobs)
        total_pages = (total_mobs + per_page - 1) // per_page

        if page < 1 or page > total_pages:
            return {"error": f"Invalid page number. Valid pages: 1-{total_pages}"}

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_mobs = all_mobs[start_idx:end_idx]

        # Group by rarity for display
        grouped_mobs = defaultdict(list)
        for rarity, mob_name in page_mobs:
            grouped_mobs[rarity].append(mob_name)

        return {"total_mobs": total_mobs, "total_pages": total_pages, "current_page": page, "mobs": dict(grouped_mobs)}

    def get_mobs_by_rarity(self, rarity: str) -> Dict[str, Any]:
        """Get mobs filtered by rarity."""
        rarity = rarity.capitalize()
        if rarity not in self.mobs_by_rarity:
            valid = ", ".join(self.mobs_by_rarity.keys())
            return {"error": f"Invalid rarity. Valid options: {valid}"}

        mob_ids = self.mobs_by_rarity[rarity]
        mob_names = [self.mobs[mob_id]["name"] for mob_id in mob_ids]

        return {"rarity": rarity, "mobs": mob_names, "count": len(mob_names)}

    def get_mob_info(self, mob_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific mob."""
        mob_id = mob_id.lower()
        return self.mobs.get(mob_id)

    def calculate_collection_value_score(self, rows: List[Dict[str, Any]]) -> int:
        """Calculate a weighted collection value score for a user's unique mobs."""
        if not rows:
            return 0

        score = 0.0
        rarity_counts: Dict[str, int] = defaultdict(int)

        for row in rows:
            mob = self.mobs.get(row["mob_id"])
            if not mob:
                continue

            rarity = mob["rarity"]
            rarity_count = len(self.mobs_by_rarity.get(rarity, []))
            if rarity_count == 0:
                continue

            score += RARITY_BUCKET_TOTALS.get(rarity, 0) / rarity_count
            rarity_counts[rarity] += 1

        for rarity, owned_count in rarity_counts.items():
            if owned_count == len(self.mobs_by_rarity.get(rarity, [])):
                score += RARITY_COMPLETION_BONUS.get(rarity, 0)

        if len(rows) == len(self.mobs):
            score += FULL_COLLECTION_BONUS

        return int(round(score))

    def get_leaderboards(self, session_factory, guild_id: int, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Return leaderboard data for emeralds, collection completion, and weighted collection value."""
        with session_factory() as session:
            user_results = session.query(UserModel.user_id, UserModel.emeralds).filter_by(guild_id=guild_id).all()
            collection_results = (
                session.query(CollectionModel.user_id, CollectionModel.mob_id, CollectionModel.amount)
                .filter_by(guild_id=guild_id)
                .all()
            )

        emerald_by_user = {user_id: emeralds for user_id, emeralds in user_results}
        collection_by_user: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for user_id, mob_id, amount in collection_results:
            collection_by_user[user_id].append({"mob_id": mob_id, "amount": amount})

        user_ids = set(emerald_by_user) | set(collection_by_user)
        users: List[Dict[str, Any]] = []
        for user_id in user_ids:
            rows = collection_by_user.get(user_id, [])
            users.append(
                {
                    "user_id": user_id,
                    "emeralds": emerald_by_user.get(user_id, 0),
                    "unique_count": len(rows),
                    "total_count": sum(entry["amount"] for entry in rows),
                    "collection_value": self.calculate_collection_value_score(rows),
                }
            )

        emerald_ranking = sorted(users, key=lambda u: u["emeralds"], reverse=True)[:limit]
        completion_ranking = sorted(
            users,
            key=lambda u: (u["unique_count"], u["total_count"]),
            reverse=True,
        )[:limit]
        value_ranking = sorted(users, key=lambda u: u["collection_value"], reverse=True)[:limit]

        return {
            "emeralds": emerald_ranking,
            "completion": completion_ranking,
            "value": value_ranking,
        }

    def build_collection_embed_data(
        self,
        rows: List[Dict[str, Any]],
        page: int = 1,
        per_page: int = 10,
        rarity_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build data for collection embed."""
        rarity_order = ["Legendary", "Epic", "Rare", "Uncommon", "Common"]
        entries = []
        for r in rarity_order:
            if rarity_filter is not None and r.lower() != rarity_filter.lower():
                continue
            for row in rows:
                mob = self.mobs[row["mob_id"]]
                if mob["rarity"] == r:
                    entries.append((r, f"{mob['name']} x{row['amount']}"))

        if rarity_filter is not None and not entries:
            valid = ", ".join(rarity_order)
            return {"error": f"No mobs found for rarity '{rarity_filter}'. Valid options: {valid}"}

        total_entries = len(entries)
        total_pages = (total_entries + per_page - 1) // per_page
        if total_pages == 0:
            total_pages = 1

        if page < 1 or page > total_pages:
            return {"error": f"Page must be between 1 and {total_pages}."}

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_entries = entries[start_idx:end_idx]

        # Group entries by rarity
        grouped_entries = defaultdict(list)
        for rarity_name, entry in page_entries:
            grouped_entries[rarity_name].append(entry)

        return {
            "total_entries": total_entries,
            "total_pages": total_pages,
            "current_page": page,
            "rarity_filter": rarity_filter,
            "entries": dict(grouped_entries),
        }
