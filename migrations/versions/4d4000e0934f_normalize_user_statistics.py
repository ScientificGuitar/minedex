"""normalize_user_statistics

Revision ID: 4d4000e0934f
Revises: 3c3000e0934e
Create Date: 2026-04-24 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d4000e0934f'
down_revision: Union[str, Sequence[str], None] = '3c3000e0934e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create user_statistics table
    op.create_table('user_statistics',
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('total_rolls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_farmer_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cleric_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_mobs_traded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_emeralds_gained', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['guild_id', 'user_id'], ['users.guild_id', 'users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('guild_id', 'user_id')
    )

    # 2. Copy data from users to user_statistics
    # We use execute to run raw SQL for the data migration
    op.execute("""
        INSERT INTO user_statistics (guild_id, user_id, total_rolls, total_claims, total_farmer_trades, total_cleric_trades, total_emeralds_gained)
        SELECT guild_id, user_id, total_rolls, total_claims, total_farmer_trades, total_cleric_trades, total_emeralds_gained
        FROM users
    """)

    # 3. Drop legacy columns from users
    # Note: 'timezone' column was removed from model but might exist in DB from previous migration 8705d827fc13
    op.drop_column('users', 'total_rolls')
    op.drop_column('users', 'total_claims')
    op.drop_column('users', 'total_farmer_trades')
    op.drop_column('users', 'total_cleric_trades')
    op.drop_column('users', 'total_emeralds_gained')
    op.drop_column('users', 'timezone')


def downgrade() -> None:
    # Restore columns to users
    op.add_column('users', sa.Column('timezone', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('total_emeralds_gained', sa.INTEGER(), autoincrement=False, nullable=False, server_default='0'))
    op.add_column('users', sa.Column('total_cleric_trades', sa.INTEGER(), autoincrement=False, nullable=False, server_default='0'))
    op.add_column('users', sa.Column('total_farmer_trades', sa.INTEGER(), autoincrement=False, nullable=False, server_default='0'))
    op.add_column('users', sa.Column('total_claims', sa.INTEGER(), autoincrement=False, nullable=False, server_default='0'))
    op.add_column('users', sa.Column('total_rolls', sa.INTEGER(), autoincrement=False, nullable=False, server_default='0'))

    # Copy data back
    op.execute("""
        UPDATE users
        SET total_rolls = s.total_rolls,
            total_claims = s.total_claims,
            total_farmer_trades = s.total_farmer_trades,
            total_cleric_trades = s.total_cleric_trades,
            total_emeralds_gained = s.total_emeralds_gained
        FROM user_statistics s
        WHERE users.guild_id = s.guild_id AND users.user_id = s.user_id
    """)

    # Drop user_statistics table
    op.drop_table('user_statistics')
