"""add_raid_announcement_fields

Revision ID: 1a2b3c4d5e6f
Revises: 0f6850d66db4
Create Date: 2026-05-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '0f6850d66db4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('raids', sa.Column('is_announced', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('raids', sa.Column('start_channel_id', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('raids', 'start_channel_id')
    op.drop_column('raids', 'is_announced')
