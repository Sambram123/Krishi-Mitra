"""add consents table and save_history column

Revision ID: ba5e3cdb8f27
Revises: c5fab0e0e9af
Create Date: 2026-10-31 05:41:27.323678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba5e3cdb8f27'
down_revision: Union[str, Sequence[str], None] = 'c5fab0e0e9af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('save_history', sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        'consents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('purpose', sa.String(length=64), nullable=False),
        sa.Column('policy_version', sa.String(length=32), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_agent', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consents_user_id'), 'consents', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_consents_user_id'), table_name='consents')
    op.drop_table('consents')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('save_history')
