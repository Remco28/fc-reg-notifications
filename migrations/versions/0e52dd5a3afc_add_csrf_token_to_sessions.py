"""add csrf token to sessions

Revision ID: 0e52dd5a3afc
Revises: 2ba564e47b5d
Create Date: 2025-10-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import secrets


# revision identifiers, used by Alembic.
revision: str = "0e52dd5a3afc"
down_revision: Union[str, Sequence[str], None] = "2ba564e47b5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user_sessions",
        sa.Column("csrf_token", sa.String(length=128), nullable=True),
    )

    bind = op.get_bind()
    result = bind.execute(sa.text("SELECT id FROM user_sessions"))
    rows = result.fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE user_sessions SET csrf_token = :token WHERE id = :id"),
            {"token": secrets.token_hex(32), "id": row.id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user_sessions", "csrf_token")
