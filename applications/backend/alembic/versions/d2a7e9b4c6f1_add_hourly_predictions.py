from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2a7e9b4c6f1"
down_revision: Union[str, Sequence[str], None] = "c8f2d4a6e1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hourly_predictions",
        sa.Column("system_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hour_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("predicted_energy_wh", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["system_id"], ["pv_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("system_id", "hour_start", "kind"),
    )


def downgrade() -> None:
    op.drop_table("hourly_predictions")
