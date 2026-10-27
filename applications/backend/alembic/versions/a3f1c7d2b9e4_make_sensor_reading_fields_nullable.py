from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1c7d2b9e4'
down_revision: Union[str, Sequence[str], None] = '819a1a218c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NULLABLE_COLUMNS = ('power_w', 'panel_temp_c', 'ambient_temp_c', 'ambient_humidity_pct')


def upgrade() -> None:
    for column in NULLABLE_COLUMNS:
        op.alter_column('sensor_readings', column, existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    for column in NULLABLE_COLUMNS:
        op.alter_column('sensor_readings', column, existing_type=sa.Float(), nullable=False)
