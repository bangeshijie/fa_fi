"""add financial import and template permissions

Revision ID: l5m6n7o8p9q0
Revises: k4l5m6n7o8p9
Create Date: 2026-11-09
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "l5m6n7o8p9q0"
down_revision: Union[str, Sequence[str], None] = "k4l5m6n7o8p9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now()
    permission_rows = [
        (
            "AccountingVoucherDetail",
            6,
            "导入会计凭证明细",
            "module_financial:accounting_voucher_detail:import",
        ),
        (
            "AccountingVoucherDetail",
            7,
            "下载会计凭证明细模板",
            "module_financial:accounting_voucher_detail:download",
        ),
        (
            "BudgetDetail",
            6,
            "导入预算明细",
            "module_financial:budget_detail:import",
        ),
        (
            "BudgetDetail",
            7,
            "下载预算明细模板",
            "module_financial:budget_detail:download",
        ),
    ]
    for route_name, menu_order, name, permission in permission_rows:
        parent_id = connection.execute(
            sa.text(
                "SELECT id FROM sys_menu "
                "WHERE route_name = :route_name AND type = 2 AND is_deleted = false LIMIT 1"
            ),
            {"route_name": route_name},
        ).scalar_one_or_none()
        if parent_id is None:
            continue
        exists = connection.execute(
            sa.text(
                "SELECT id FROM sys_menu "
                "WHERE permission = :permission AND is_deleted = false LIMIT 1"
            ),
            {"permission": permission},
        ).scalar_one_or_none()
        if exists is not None:
            continue
        connection.execute(
            sa.text(
                """
                INSERT INTO sys_menu (
                    name, type, "order", permission, icon, route_name, route_path,
                    component_path, redirect, hidden, keep_alive, always_show, title,
                    params, affix, client, parent_id, uuid, status, description,
                    created_time, updated_time, is_deleted, deleted_time
                ) VALUES (
                    :name, 3, :menu_order, :permission, NULL, NULL, NULL,
                    NULL, NULL, false, true, false, :name,
                    NULL, false, 'pc', :parent_id, :uuid, '0', '财务模块初始化',
                    :created_time, :updated_time, false, NULL
                )
                """
            ),
            {
                "name": name,
                "menu_order": menu_order,
                "permission": permission,
                "parent_id": parent_id,
                "uuid": str(uuid4()),
                "created_time": now,
                "updated_time": now,
            },
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM sys_menu WHERE permission IN ("
            "'module_financial:accounting_voucher_detail:import', "
            "'module_financial:accounting_voucher_detail:download', "
            "'module_financial:budget_detail:import', "
            "'module_financial:budget_detail:download'"
            ")"
        )
    )
