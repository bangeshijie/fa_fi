"""add currency amount and text fields to financial details

Revision ID: n7o8p9q0r1s2
Revises: m6n7o8p9q0r1
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "n7o8p9q0r1s2"
down_revision: Union[str, Sequence[str], None] = "m6n7o8p9q0r1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_financial_columns(table_name: str, text_column: str, text_comment: str) -> None:
    op.add_column(
        table_name,
        sa.Column(
            "currency",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'RMB'"),
            comment="币种",
        ),
    )
    op.add_column(
        table_name,
        sa.Column(
            "amount",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            server_default=sa.text("0"),
            comment="金额",
        ),
    )
    op.add_column(
        table_name,
        sa.Column(text_column, sa.Text(), nullable=True, comment=text_comment),
    )
    op.alter_column(table_name, "amount", server_default=None)


def upgrade() -> None:
    _add_financial_columns(
        "fin_accounting_voucher_detail", "voucher_text", "凭证文本"
    )
    op.add_column(
        "fin_accounting_voucher_detail",
        sa.Column(
            "debit_credit_direction",
            sa.String(length=4),
            nullable=False,
            server_default=sa.text("'借'"),
            comment="借贷方向",
        ),
    )
    op.alter_column(
        "fin_accounting_voucher_detail", "debit_credit_direction", server_default=None
    )
    _add_financial_columns("fin_budget_detail", "budget_text", "预算文本")


def downgrade() -> None:
    for table_name, text_column in (
        ("fin_budget_detail", "budget_text"),
        ("fin_accounting_voucher_detail", "voucher_text"),
    ):
        if table_name == "fin_accounting_voucher_detail":
            op.drop_column(table_name, "debit_credit_direction")
        op.drop_column(table_name, text_column)
        op.drop_column(table_name, "amount")
        op.drop_column(table_name, "currency")
