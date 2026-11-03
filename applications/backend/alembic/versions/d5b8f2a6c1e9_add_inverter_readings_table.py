from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5b8f2a6c1e9'
down_revision: Union[str, Sequence[str], None] = 'c4a9e1f7d3b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('inverter_readings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('system_id', sa.UUID(), nullable=False),
    sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('source', sa.String(length=16), nullable=False),
    sa.Column('power_w', sa.Float(), nullable=True),
    sa.Column('dc_power_w', sa.Float(), nullable=True),
    sa.Column('daily_yield_wh', sa.Float(), nullable=True),
    sa.Column('total_yield_wh', sa.Float(), nullable=True),
    sa.Column('internal_temp_c', sa.Float(), nullable=True),
    sa.Column('grid_frequency_hz', sa.Float(), nullable=True),
    sa.Column('status_code', sa.Integer(), nullable=True),
    sa.Column('mppt1_voltage_v', sa.Float(), nullable=True),
    sa.Column('mppt1_current_a', sa.Float(), nullable=True),
    sa.Column('mppt2_voltage_v', sa.Float(), nullable=True),
    sa.Column('mppt2_current_a', sa.Float(), nullable=True),
    sa.Column('mppt3_voltage_v', sa.Float(), nullable=True),
    sa.Column('mppt3_current_a', sa.Float(), nullable=True),
    sa.Column('mppt4_voltage_v', sa.Float(), nullable=True),
    sa.Column('mppt4_current_a', sa.Float(), nullable=True),
    sa.CheckConstraint("source IN ('cloud', 'modbus')", name='ck_inverter_readings_source'),
    sa.ForeignKeyConstraint(['system_id'], ['pv_systems.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('system_id', 'recorded_at', 'source', name='uq_inverter_readings_system_recorded_source')
    )


def downgrade() -> None:
    op.drop_table('inverter_readings')
