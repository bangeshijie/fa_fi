"""fix financial directory menu redirect

Revision ID: k4l5m6n7o8p9
Revises: j3k4l5m6n7
Create Date: 2026-11-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "k4l5m6n7o8p9"
down_revision: Union[str, Sequence[str], None] = "j3k4l5m6n7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE sys_menu "
            "SET redirect = :redirect "
            "WHERE route_name = 'Financial' AND type = 1 AND is_deleted = false"
        ).bindparams(redirect="/financial/accounting-voucher-detail")
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE sys_menu SET redirect = NULL "
            "WHERE route_name = 'Financial' AND type = 1 AND is_deleted = false"
        )
    )
