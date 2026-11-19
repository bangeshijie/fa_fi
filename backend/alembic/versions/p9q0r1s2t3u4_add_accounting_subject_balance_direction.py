"""add accounting subject balance direction

Revision ID: p9q0r1s2t3u4
Revises: o8p9q0r1s2t3
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p9q0r1s2t3u4"
down_revision: Union[str, Sequence[str], None] = "o8p9q0r1s2t3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "dim_accounting_subject",
        sa.Column(
            "balance_direction",
            sa.String(length=2),
            nullable=True,
            comment="科目余额方向(借/贷)",
        ),
    )
    op.execute(
        sa.text(
            "UPDATE dim_accounting_subject "
            "SET balance_direction = '借' "
            "WHERE balance_direction IS NULL"
        )
    )
    op.alter_column(
        "dim_accounting_subject",
        "balance_direction",
        existing_type=sa.String(length=2),
        nullable=False,
        comment="科目余额方向(借/贷)",
    )


def downgrade() -> None:
    op.drop_column("dim_accounting_subject", "balance_direction")
