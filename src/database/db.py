import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import BigInteger, Boolean, ForeignKeyConstraint, Integer, String, create_engine
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool

Base = declarative_base()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return database_url


def get_engine():
    return create_engine(get_database_url(), poolclass=NullPool, echo=False)


def get_session_local():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    session = get_session_local()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=get_engine())


class User(Base):
    __tablename__ = "users"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)

    emeralds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trading_hall_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unlocked_villagers: Mapped[str] = mapped_column(String, nullable=False, default="")

    last_roll_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_claim_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_focus_roll_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_reroll_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_daily_at: Mapped[int | None] = mapped_column(Integer, nullable=True)


class UserStatistics(Base):
    __tablename__ = "user_statistics"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)

    total_rolls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_claims: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_farmer_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cleric_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_mobs_traded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_emeralds_gained: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        ForeignKeyConstraint(
            ["guild_id", "user_id"],
            ["users.guild_id", "users.user_id"],
            ondelete="CASCADE",
        ),
    )


class Collection(Base):
    __tablename__ = "collections"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    mob_id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)

    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        ForeignKeyConstraint(
            ["guild_id", "user_id"],
            ["users.guild_id", "users.user_id"],
            ondelete="CASCADE",
        ),
    )


class Inventory(Base):
    __tablename__ = "inventory"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    item_id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)

    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        ForeignKeyConstraint(
            ["guild_id", "user_id"],
            ["users.guild_id", "users.user_id"],
            ondelete="CASCADE",
        ),
    )


class AchievementUnlock(Base):
    __tablename__ = "achievement_unlocks"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    achievement_id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)

    unlocked_at: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["guild_id", "user_id"],
            ["users.guild_id", "users.user_id"],
            ondelete="CASCADE",
        ),
    )


class Raid(Base):
    __tablename__ = "raids"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    spawned_at: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    boss_id: Mapped[str] = mapped_column(String, nullable=False)
    
    current_phase: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    target_tag: Mapped[str | None] = mapped_column(String, nullable=True)
    
    current_power: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_power: Mapped[int] = mapped_column(Integer, nullable=False)
    
    ended_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RaidContribution(Base):
    __tablename__ = "raid_contributions"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    spawned_at: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    
    total_power_donated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mobs_donated_this_phase: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["guild_id", "user_id"],
            ["users.guild_id", "users.user_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["guild_id", "spawned_at"],
            ["raids.guild_id", "raids.spawned_at"],
            ondelete="CASCADE",
        ),
    )
