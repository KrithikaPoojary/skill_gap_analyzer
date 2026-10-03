"""add user login tracking columns

Revision ID: d1b3f4a7e8c9
Revises: c9a2817d3b5e
Create Date: 2026-10-03 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1b3f4a7e8c9'
down_revision: Union[str, Sequence[str], None] = 'c9a2817d3b5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add last_login_at and login_count to users table."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('login_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema: remove login tracking columns from users table."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('login_count')
        batch_op.drop_column('last_login_at')
