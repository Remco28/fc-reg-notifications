"""add_cache_fields_to_tracked_fencers

Revision ID: f8a8c6bdf3d7
Revises: 2ba564e47b5d
Create Date: 2025-10-02 15:07:13.153756

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a8c6bdf3d7'
down_revision: Union[str, Sequence[str], None] = '2ba564e47b5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tracked_fencers', sa.Column('last_registration_hash', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tracked_fencers', 'last_registration_hash')
