"""align cost center indexes with common model fields

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-11-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("dim_cost_center", "is_frozen", server_default=None)
    op.drop_index(
        "ix_dim_cost_center_enable_time", table_name="dim_cost_center", if_exists=True
    )
    for column in ("created_time", "deleted_id", "deleted_time", "updated_id"):
        op.create_index(
            f"ix_dim_cost_center_{column}", "dim_cost_center", [column], unique=False
        )


def downgrade() -> None:
    for column in ("created_time", "deleted_id", "deleted_time", "updated_id"):
        op.drop_index(f"ix_dim_cost_center_{column}", table_name="dim_cost_center")
    op.create_index(
        "ix_dim_cost_center_enable_time", "dim_cost_center", ["enable_time"], unique=False
    )
    op.alter_column(
        "dim_cost_center", "is_frozen", server_default=sa.false()
    )
