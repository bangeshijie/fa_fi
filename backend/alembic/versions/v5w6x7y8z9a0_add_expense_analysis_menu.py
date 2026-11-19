"""add expense analysis menu

Revision ID: v5w6x7y8z9a0
Revises: u4v5w6x7y8z9
Create Date: 2026-11-12
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "v5w6x7y8z9a0"
down_revision: Union[str, Sequence[str], None] = "u4v5w6x7y8z9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    menu_count = connection.execute(sa.text("SELECT COUNT(1) FROM sys_menu")).scalar_one()
    if not menu_count:
        return

    parent_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE route_name = 'Financial' AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    if parent_id is None:
        return

    existing = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE permission = 'module_financial:expense_analysis:query' "
            "AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    if existing:
        return

    now = datetime.now()
    expense_menu_id = connection.execute(
        sa.text(
            """
            INSERT INTO sys_menu (
                name, type, "order", permission, icon, route_name, route_path,
                component_path, redirect, hidden, keep_alive, always_show, title,
                params, affix, client, parent_id, uuid, status, description,
                created_time, updated_time, is_deleted, deleted_time
            ) VALUES (
                '费用分析', 2, 2, 'module_financial:expense_analysis:query',
                'ri:line-chart-line', 'ExpenseAnalysis', 'expense-analysis',
                'module_financial/expense_analysis/index', NULL, false, true, false,
                '费用分析', NULL, false, 'pc', :parent_id, :uuid, '0',
                '财务费用分析初始化', :created_time, :updated_time, false, NULL
            ) RETURNING id
            """
        ),
        {
            "parent_id": int(parent_id),
            "uuid": str(uuid4()),
            "created_time": now,
            "updated_time": now,
        },
    ).scalar_one()

    connection.execute(
        sa.text(
            """
            INSERT INTO sys_menu (
                name, type, "order", permission, icon, route_name, route_path,
                component_path, redirect, hidden, keep_alive, always_show, title,
                params, affix, client, parent_id, uuid, status, description,
                created_time, updated_time, is_deleted, deleted_time
            ) VALUES (
                '查询费用分析', 3, 1, 'module_financial:expense_analysis:query',
                NULL, NULL, NULL, NULL, NULL, false, true, false,
                '查询费用分析', NULL, false, 'pc', :parent_id, :uuid, '0',
                '财务费用分析初始化', :created_time, :updated_time, false, NULL
            )
            """
        ),
        {
            "parent_id": int(expense_menu_id),
            "uuid": str(uuid4()),
            "created_time": now,
            "updated_time": now,
        },
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sys_menu WHERE permission = 'module_financial:expense_analysis:query' "
            "OR route_name = 'ExpenseAnalysis'"
        )
    )
