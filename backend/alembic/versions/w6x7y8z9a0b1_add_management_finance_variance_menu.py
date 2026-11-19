"""add management finance variance menu

Revision ID: w6x7y8z9a0b1
Revises: v5w6x7y8z9a0
Create Date: 2026-11-18
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "w6x7y8z9a0b1"
down_revision: Union[str, Sequence[str], None] = "v5w6x7y8z9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSION = "module_financial:management_finance_variance:query"


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
            "WHERE permission = :permission AND is_deleted = false LIMIT 1"
        ),
        {"permission": PERMISSION},
    ).scalar_one_or_none()
    if existing:
        return

    now = datetime.now()
    menu_id = connection.execute(
        sa.text(
            """
            INSERT INTO sys_menu (
                name, type, "order", permission, icon, route_name, route_path,
                component_path, redirect, hidden, keep_alive, always_show, title,
                params, affix, client, parent_id, uuid, status, description,
                created_time, updated_time, is_deleted, deleted_time
            ) VALUES (
                '管财差异分析', 2, 3, :permission,
                'ri:exchange-2-line', 'ManagementFinanceVariance', 'management-finance-variance',
                'module_financial/management_finance_variance/index', NULL, false, true, false,
                '管财差异分析', NULL, false, 'pc', :parent_id, :uuid, '0',
                '财务管财差异分析初始化', :created_time, :updated_time, false, NULL
            ) RETURNING id
            """
        ),
        {
            "permission": PERMISSION,
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
                '查询管财差异分析', 3, 1, :permission,
                NULL, NULL, NULL, NULL, NULL, false, true, false,
                '查询管财差异分析', NULL, false, 'pc', :parent_id, :uuid, '0',
                '财务管财差异分析初始化', :created_time, :updated_time, false, NULL
            )
            """
        ),
        {
            "permission": PERMISSION,
            "parent_id": int(menu_id),
            "uuid": str(uuid4()),
            "created_time": now,
            "updated_time": now,
        },
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sys_menu WHERE permission = :permission "
            "OR route_name = 'ManagementFinanceVariance'"
        ),
        {"permission": PERMISSION},
    )
