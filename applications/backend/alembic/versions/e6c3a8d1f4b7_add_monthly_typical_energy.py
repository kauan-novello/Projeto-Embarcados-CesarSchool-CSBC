from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e6c3a8d1f4b7"
down_revision: Union[str, Sequence[str], None] = "d2a7e9b4c6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monthly_typical_energy",
        sa.Column("system_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("energy_wh", sa.Float(), nullable=False),
        sa.Column("low_wh", sa.Float(), nullable=False),
        sa.Column("high_wh", sa.Float(), nullable=False),
        sa.Column("n_years", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["system_id"], ["pv_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("system_id", "month"),
    )


def downgrade() -> None:
    op.drop_table("monthly_typical_energy")
