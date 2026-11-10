from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3e7f1a9c5d4"
down_revision: Union[str, Sequence[str], None] = "a9d4e2c6f8b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("weather_readings", "station_id", type_=sa.String(length=32))
    op.alter_column("pv_systems", "weather_station_id", type_=sa.String(length=32))


def downgrade() -> None:
    op.alter_column("pv_systems", "weather_station_id", type_=sa.String(length=8))
    op.alter_column("weather_readings", "station_id", type_=sa.String(length=8))
