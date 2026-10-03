"""add skill_gap_snapshots table

Revision ID: c9a2817d3b5e
Revises: f8e516b9b0c8
Create Date: 2026-10-03 19:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9a2817d3b5e'
down_revision: Union[str, Sequence[str], None] = 'f8e516b9b0c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'skill_gap_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.Column('role_title', sa.String(length=100), nullable=False),
        sa.Column('readiness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('matched_skills', sa.JSON(), nullable=False),
        sa.Column('missing_skills', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['target_roles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('skill_gap_snapshots', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_gap_snapshots_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('skill_gap_snapshots', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_gap_snapshots_user_id'))

    op.drop_table('skill_gap_snapshots')
