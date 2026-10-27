from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7c3a9d1f4b6'
down_revision: Union[str, Sequence[str], None] = 'd5b8f2a6c1e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'devices',
        sa.Column('id', sa.String(length=12), nullable=False),
        sa.Column('system_id', sa.UUID(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('pairing_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['system_id'], ['pv_systems.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system_id'),
    )
    op.drop_index(op.f('ix_pv_systems_pairing_code'), table_name='pv_systems')
    op.drop_column('pv_systems', 'pairing_code')
    op.drop_column('pv_systems', 'device_online')


def downgrade() -> None:
    op.add_column(
        'pv_systems',
        sa.Column('device_online', sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column('pv_systems', sa.Column('pairing_code', sa.String(length=16), nullable=True))
    op.execute("UPDATE pv_systems SET pairing_code = 'SLR-' || upper(substr(md5(id::text), 1, 4))")
    op.alter_column('pv_systems', 'pairing_code', nullable=False)
    op.create_index(op.f('ix_pv_systems_pairing_code'), 'pv_systems', ['pairing_code'], unique=True)
    op.drop_table('devices')
