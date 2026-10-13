from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '073c57845a71'
down_revision: Union[str, Sequence[str], None] = '4d649453497d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pv_systems', sa.Column('pairing_code', sa.String(length=16), nullable=False))
    op.create_index(op.f('ix_pv_systems_pairing_code'), 'pv_systems', ['pairing_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_pv_systems_pairing_code'), table_name='pv_systems')
    op.drop_column('pv_systems', 'pairing_code')
