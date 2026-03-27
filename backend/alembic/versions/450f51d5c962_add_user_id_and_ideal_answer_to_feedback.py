"""add user_id and ideal_answer to feedback

Revision ID: 450f51d5c962
Revises: 73649092144b
Create Date: 2026-03-27 23:33:31.377399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '450f51d5c962'
down_revision: Union[str, Sequence[str], None] = '73649092144b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('feedbacks', sa.Column('user_id', sa.Integer(), nullable=True))   # ← nullable=True for SQLite
    op.add_column('feedbacks', sa.Column('ideal_answer', sa.Text(), nullable=True))
    # op.alter_column removed — SQLite doesn't support ALTER COLUMN
    # op.create_foreign_key removed — SQLite doesn't enforce FK constraints


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('feedbacks', 'ideal_answer')
    op.drop_column('feedbacks', 'user_id')