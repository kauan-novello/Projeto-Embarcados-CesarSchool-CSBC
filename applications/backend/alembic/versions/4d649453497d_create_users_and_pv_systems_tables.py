from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4d649453497d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('pv_systems',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=False),
    sa.Column('installed_power_kw', sa.Float(), nullable=False),
    sa.Column('inverter_type', sa.Enum('ON_GRID', 'OFF_GRID', name='invertertype'), nullable=False),
    sa.Column('status', sa.Enum('AWAITING_PAIRING', 'ONLINE_UNTRAINED', 'TRAINING', 'MODEL_ACTIVE', name='systemstatus'), nullable=False),
    sa.Column('training_started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('photo_url', sa.String(), nullable=True),
    sa.Column('device_online', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('pv_systems')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
