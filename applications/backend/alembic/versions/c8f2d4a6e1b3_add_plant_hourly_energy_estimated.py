from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8f2d4a6e1b3"
down_revision: Union[str, Sequence[str], None] = "b3e7f1a9c5d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "plant_hourly",
        sa.Column("energy_estimated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("plant_hourly", "energy_estimated")
