"""align cost center enable date comment

Revision ID: g0a1b2c3d4e5f6
Revises: f0a1b2c3d4e5
Create Date: 2026-11-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g0a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "dim_cost_center",
        "enable_time",
        existing_type=sa.Date(),
        existing_nullable=False,
        comment="启用日期",
    )


def downgrade() -> None:
    op.alter_column(
        "dim_cost_center",
        "enable_time",
        existing_type=sa.Date(),
        existing_nullable=False,
        comment="启用时间",
    )
