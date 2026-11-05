from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a9d4e2c6f8b1"
down_revision: Union[str, Sequence[str], None] = "f1a8c3e5b7d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("weather_readings", sa.Column("pressure_hpa", sa.Float(), nullable=True))
    op.add_column("weather_readings", sa.Column("wind_speed_m_s", sa.Float(), nullable=True))
    op.create_table(
        "plant_hourly",
        sa.Column("system_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hour_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("energy_wh", sa.Float(), nullable=False),
        sa.Column("radiation_wh_m2", sa.Float(), nullable=False),
        sa.Column("air_temp_c", sa.Float(), nullable=False),
        sa.Column("humidity_pct", sa.Float(), nullable=False),
        sa.Column("humidity_estimated", sa.Boolean(), nullable=False),
        sa.Column("pressure_hpa", sa.Float(), nullable=False),
        sa.Column("wind_speed_m_s", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["system_id"], ["pv_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("system_id", "hour_start"),
    )


def downgrade() -> None:
    op.drop_table("plant_hourly")
    op.drop_column("weather_readings", "wind_speed_m_s")
    op.drop_column("weather_readings", "pressure_hpa")
