from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .db import User as UserModel


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

            return same_utc_day(user.last_focus_roll_at, now_ts, user.timezone)

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
    def get_trading_hall_level(session_factory, guild_id: int, user_id: int) -> int | None:
        """Get the trading hall level for a user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            return user.trading_hall_level if user else None

    @staticmethod
    def upgrade_trading_hall(session_factory, guild_id: int, user_id: int) -> None:
        """Upgrade a user's trading hall level."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.trading_hall_level += 1
                session.commit()

    @staticmethod
    def get_timezone(session_factory, guild_id: int, user_id: int) -> str | None:
        """Get the timezone for a user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            return user.timezone if user else None

    @staticmethod
    def set_timezone(session_factory, guild_id: int, user_id: int, timezone: str) -> None:
        """Set the timezone for a user."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.timezone = timezone
                session.commit()

    @staticmethod
    def increment_total_rolls(session_factory, guild_id: int, user_id: int) -> None:
        """Increment the total rolls counter."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.total_rolls += 1
                session.commit()

    @staticmethod
    def increment_total_claims(session_factory, guild_id: int, user_id: int) -> None:
        """Increment the total claims counter."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.total_claims += 1
                session.commit()

    @staticmethod
    def increment_total_farmer_trades(session_factory, guild_id: int, user_id: int) -> None:
        """Increment the total farmer trades counter."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.total_farmer_trades += 1
                session.commit()

    @staticmethod
    def increment_total_cleric_trades(session_factory, guild_id: int, user_id: int) -> None:
        """Increment the total cleric trades counter."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.total_cleric_trades += 1
                session.commit()

    @staticmethod
    def add_emeralds_gained(session_factory, guild_id: int, user_id: int, amount: int) -> None:
        """Add to the total emeralds gained (for stats tracking)."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.total_emeralds_gained += amount
                session.commit()

    @staticmethod
    def add_mobs_traded(session_factory, guild_id: int, user_id: int, amount: int) -> None:
        """Add to the total mobs traded counter."""
        with session_factory() as session:
            user = session.query(UserModel).filter_by(guild_id=guild_id, user_id=user_id).first()
            if user:
                user.total_mobs_traded += amount
                session.commit()


def same_utc_day(ts1: int | None, ts2: int | None, tz_str: str | None = None) -> bool:
    """Check if two timestamps are on the same day in the given timezone (or UTC if None)."""
    if ts1 is None or ts2 is None:
        return False

    tz = ZoneInfo(tz_str) if tz_str else timezone.utc

    d1 = datetime.fromtimestamp(ts1, tz=tz).date()
    d2 = datetime.fromtimestamp(ts2, tz=tz).date()
    return d1 == d2
