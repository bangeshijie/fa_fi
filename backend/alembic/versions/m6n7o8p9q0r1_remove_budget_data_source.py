"""remove redundant budget data source column

Revision ID: m6n7o8p9q0r1
Revises: l5m6n7o8p9q0
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "m6n7o8p9q0r1"
down_revision: Union[str, Sequence[str], None] = "l5m6n7o8p9q0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text("ALTER TABLE fin_budget_detail DROP COLUMN IF EXISTS data_source")
    )


def downgrade() -> None:
    op.add_column(
        "fin_budget_detail",
        sa.Column("data_source", sa.String(length=128), nullable=True, comment="数据来源"),
    )
