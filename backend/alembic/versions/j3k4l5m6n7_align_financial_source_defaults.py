"""align financial source category defaults

Revision ID: j3k4l5m6n7
Revises: i2j3k4l5m6n7
Create Date: 2026-11-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j3k4l5m6n7"
down_revision: Union[str, Sequence[str], None] = "i2j3k4l5m6n7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "fin_accounting_voucher_detail",
        "data_source_category",
        existing_type=sa.String(length=32),
        existing_nullable=False,
        server_default=sa.text("'SAP原始明细'"),
    )
    op.alter_column(
        "fin_budget_detail",
        "data_source_category",
        existing_type=sa.String(length=16),
        existing_nullable=False,
        server_default=sa.text("'原始'"),
    )


def downgrade() -> None:
    op.alter_column(
        "fin_accounting_voucher_detail",
        "data_source_category",
        existing_type=sa.String(length=32),
        existing_nullable=False,
        server_default=None,
    )
    op.alter_column(
        "fin_budget_detail",
        "data_source_category",
        existing_type=sa.String(length=16),
        existing_nullable=False,
        server_default=None,
    )
