from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e2d4f8a1c6'
down_revision: Union[str, Sequence[str], None] = 'a3f1c7d2b9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sensor_readings', sa.Column('pressure_hpa', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('sensor_readings', 'pressure_hpa')
