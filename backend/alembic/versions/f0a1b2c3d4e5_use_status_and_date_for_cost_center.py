"""use common status and date for cost center

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-11-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "e9f0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_dim_cost_center_is_frozen", table_name="dim_cost_center", if_exists=True)
    op.drop_column("dim_cost_center", "is_frozen")
    op.alter_column(
        "dim_cost_center",
        "enable_time",
        existing_type=sa.DateTime(),
        type_=sa.Date(),
        existing_nullable=False,
        comment="启用日期",
    )
    op.execute(
        sa.text(
            "UPDATE sys_menu SET name = :name, title = :name "
            "WHERE permission = :permission AND is_deleted = false"
        ).bindparams(
            name="修改成本中心状态", permission="module_dimension:cost_center:patch"
        )
    )


def downgrade() -> None:
    op.alter_column(
        "dim_cost_center",
        "enable_time",
        existing_type=sa.Date(),
        type_=sa.DateTime(),
        existing_nullable=False,
        comment="启用时间",
    )
    op.add_column(
        "dim_cost_center",
        sa.Column(
            "is_frozen",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="是否冻结(0:否 1:是)",
        ),
    )
    op.create_index(
        "ix_dim_cost_center_is_frozen", "dim_cost_center", ["is_frozen"], unique=False
    )
    op.execute(
        sa.text(
            "UPDATE sys_menu SET name = :name, title = :name "
            "WHERE permission = :permission AND is_deleted = false"
        ).bindparams(
            name="修改成本中心冻结状态", permission="module_dimension:cost_center:patch"
        )
    )
