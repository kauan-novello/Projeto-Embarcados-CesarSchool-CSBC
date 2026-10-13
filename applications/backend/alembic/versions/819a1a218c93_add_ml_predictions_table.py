from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '819a1a218c93'
down_revision: Union[str, Sequence[str], None] = '2efdd77a5404'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ml_predictions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('system_id', sa.UUID(), nullable=False),
    sa.Column('predicted_efficiency_pct', sa.Float(), nullable=False),
    sa.Column('predicted_generation_kwh_next_day', sa.Float(), nullable=False),
    sa.Column('model_version', sa.String(length=120), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['system_id'], ['pv_systems.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ml_predictions')
