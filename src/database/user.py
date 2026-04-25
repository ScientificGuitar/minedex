from datetime import datetime, time, timezone

from constants import GLOBAL_RESET_HOUR
from .db import User as UserModel, UserStatistics as StatsModel


class User:
    @staticmethod
    def ensure_user(session_factory, guild_id: int, user_id: int) -> None:
        """Ensure a user exists in the database, creating if necessary."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if not user:
                user = UserModel(guild_id=guild_id, user_id=user_id)
                session.add(user)
                session.commit()
            
            # Also ensure stats entry exists
            User.ensure_stats(session_factory, guild_id, user_id)

    @staticmethod
    def get_user(session_factory, guild_id: int, user_id: int) -> UserModel | None:
        """Get a user by guild_id and user_id."""
        with session_factory() as session:
            return session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()

    @staticmethod
    def has_focus_rolled_today(session_factory, guild_id: int, user_id: int, now_ts: int) -> bool:
        """Check if user has already focus rolled today."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()

            if user is None or user.last_focus_roll_at is None:
                return False

            return is_same_game_day(user.last_focus_roll_at, now_ts)

    @staticmethod
    def record_roll(session_factory, guild_id: int, user_id: int, now_ts: int) -> None:
        """Record a roll timestamp for the user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.last_roll_at = now_ts
                session.commit()

    @staticmethod
    def record_reroll(session_factory, guild_id: int, user_id: int, now_ts: int) -> None:
        """Record a reroll timestamp for the user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.last_reroll_at = now_ts
                session.commit()

    @staticmethod
    def record_focus_roll(session_factory, guild_id: int, user_id: int, now_ts: int) -> None:
        """Record a focus roll timestamp for the user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.last_focus_roll_at = now_ts
                session.commit()

    @staticmethod
    def update_last_claim_at(session_factory, guild_id: int, user_id: int, timestamp: int) -> None:
        """Update the last claim timestamp."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.last_claim_at = timestamp
                session.commit()

    @staticmethod
    def update_last_daily_at(session_factory, guild_id: int, user_id: int, timestamp: int) -> None:
        """Update the last daily command timestamp."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.last_daily_at = timestamp
                session.commit()

    @staticmethod
    def add_emeralds(session_factory, guild_id: int, user_id: int, amount: int) -> None:
        """Add emeralds to a user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.emeralds += amount
                session.commit()

    @staticmethod
    def get_emeralds(session_factory, guild_id: int, user_id: int) -> int | None:
        """Get the number of emeralds a user has."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            return user.emeralds if user else None

    @staticmethod
    def get_unlocked_villagers(session_factory, guild_id: int, user_id: int) -> list[str]:
        """Get the list of unlocked villager IDs for a user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if not user or not user.unlocked_villagers:
                return []
            return [v.strip() for v in user.unlocked_villagers.split(",") if v.strip()]

    @staticmethod
    def unlock_villager(session_factory, guild_id: int, user_id: int, villager_id: str) -> None:
        """Unlock a villager for a user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                unlocked = User.get_unlocked_villagers(session_factory, guild_id, user_id)
                if villager_id not in unlocked:
                    unlocked.append(villager_id)
                    user.unlocked_villagers = ",".join(unlocked)
                    user.trading_hall_level = len(unlocked)
                session.commit()

    @staticmethod
    def is_villager_unlocked(session_factory, guild_id: int, user_id: int, villager_id: str) -> bool:
        """Check if a villager is unlocked for a user."""
        unlocked = User.get_unlocked_villagers(session_factory, guild_id, user_id)
        return villager_id in unlocked

    @staticmethod
    def ensure_stats(session_factory, guild_id: int, user_id: int) -> None:
        """Ensure stats entry exists for user."""
        with session_factory() as session:
            stats = session.query(StatsModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if not stats:
                stats = StatsModel(guild_id=guild_id, user_id=user_id)
                session.add(stats)
                session.commit()

    @staticmethod
    def get_stats(session_factory, guild_id: int, user_id: int) -> StatsModel | None:
        """Get user statistics."""
        with session_factory() as session:
            return session.query(StatsModel).filter_by(guild_id=guild_id, user_id=user_id).first()

    @staticmethod
    def increment_total_rolls(session_factory, guild_id: int, user_id: int) -> None:
        """Increment the total rolls counter."""
        User.ensure_stats(session_factory, guild_id, user_id)
        with session_factory() as session:
            stats = session.query(StatsModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if stats:
                stats.total_rolls += 1
                session.commit()

    @staticmethod
    def increment_total_claims(session_factory, guild_id: int, user_id: int) -> None:
        """Increment the total claims counter."""
        User.ensure_stats(session_factory, guild_id, user_id)
        with session_factory() as session:
            stats = session.query(StatsModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if stats:
                stats.total_claims += 1
                session.commit()

    @staticmethod
    def increment_total_farmer_trades(session_factory, guild_id: int, user_id: int) -> None:
        """Increment the total farmer trades counter."""
        User.ensure_stats(session_factory, guild_id, user_id)
        with session_factory() as session:
            stats = session.query(StatsModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if stats:
                stats.total_farmer_trades += 1
                session.commit()

    @staticmethod
    def increment_total_cleric_trades(session_factory, guild_id: int, user_id: int) -> None:
        """Increment the total cleric trades counter."""
        User.ensure_stats(session_factory, guild_id, user_id)
        with session_factory() as session:
            stats = session.query(StatsModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if stats:
                stats.total_cleric_trades += 1
                session.commit()

    @staticmethod
    def add_emeralds_gained(session_factory, guild_id: int, user_id: int, amount: int) -> None:
        """Add to the total emeralds gained (for stats tracking)."""
        User.ensure_stats(session_factory, guild_id, user_id)
        with session_factory() as session:
            stats = session.query(StatsModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if stats:
                stats.total_emeralds_gained += amount
                session.commit()

    @staticmethod
    def add_mobs_traded(session_factory, guild_id: int, user_id: int, amount: int) -> None:
        """Add to the total mobs traded counter."""
        User.ensure_stats(session_factory, guild_id, user_id)
        with session_factory() as session:
            stats = session.query(StatsModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if stats:
                stats.total_mobs_traded += amount
                session.commit()


def is_same_game_day(ts1: int | None, ts2: int | None) -> bool:
    """Check if two timestamps are in the same game day (resetting at GLOBAL_RESET_HOUR UTC)."""
    if ts1 is None or ts2 is None:
        return False

    dt1 = datetime.fromtimestamp(ts1, tz=timezone.utc)
    dt2 = datetime.fromtimestamp(ts2, tz=timezone.utc)

    # Adjusted date: if time is before reset hour, it belongs to the previous calendar day
    def get_game_date(dt: datetime):
        if dt.hour < GLOBAL_RESET_HOUR:
            return dt.date().toordinal() - 1
        return dt.date().toordinal()

    return get_game_date(dt1) == get_game_date(dt2)
