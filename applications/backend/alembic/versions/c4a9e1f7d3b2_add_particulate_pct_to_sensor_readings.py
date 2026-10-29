from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4a9e1f7d3b2'
down_revision: Union[str, Sequence[str], None] = 'b7e2d4f8a1c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sensor_readings', sa.Column('particulate_pct', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('sensor_readings', 'particulate_pct')
