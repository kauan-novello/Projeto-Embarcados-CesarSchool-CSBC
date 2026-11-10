from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a8c3e5b7d2"
down_revision: Union[str, Sequence[str], None] = "e7c3a9d1f4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weather_readings",
        sa.Column("station_id", sa.String(length=8), nullable=False),
        sa.Column("hour_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("radiation_wh_m2", sa.Float(), nullable=True),
        sa.Column("air_temp_c", sa.Float(), nullable=True),
        sa.Column("humidity_pct", sa.Float(), nullable=True),
        sa.Column("precipitation_mm", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("station_id", "hour_start"),
    )
    op.add_column("pv_systems", sa.Column("weather_station_id", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("pv_systems", "weather_station_id")
    op.drop_table("weather_readings")
