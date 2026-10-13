from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2efdd77a5404'
down_revision: Union[str, Sequence[str], None] = '073c57845a71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('overheat_alerts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('system_id', sa.UUID(), nullable=False),
    sa.Column('panel_temp_c', sa.Float(), nullable=False),
    sa.Column('threshold_c', sa.Float(), nullable=False),
    sa.Column('email_to', sa.String(), nullable=True),
    sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['system_id'], ['pv_systems.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sensor_readings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('system_id', sa.UUID(), nullable=False),
    sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('power_w', sa.Float(), nullable=False),
    sa.Column('panel_temp_c', sa.Float(), nullable=False),
    sa.Column('ambient_temp_c', sa.Float(), nullable=False),
    sa.Column('ambient_humidity_pct', sa.Float(), nullable=False),
    sa.Column('irradiance', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['system_id'], ['pv_systems.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sensor_readings_system_id_recorded_at', 'sensor_readings', ['system_id', 'recorded_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_sensor_readings_system_id_recorded_at', table_name='sensor_readings')
    op.drop_table('sensor_readings')
    op.drop_table('overheat_alerts')
