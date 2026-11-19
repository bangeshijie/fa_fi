"""move budget detail into the parallel budget module

Revision ID: o8p9q0r1s2t3
Revises: n7o8p9q0r1s2
Create Date: 2026-11-10
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "o8p9q0r1s2t3"
down_revision: Union[str, Sequence[str], None] = "n7o8p9q0r1s2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _insert_budget_root(connection: sa.Connection) -> int:
    existing = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE route_name = 'Budget' AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    if existing is not None:
        return int(existing)

    now = datetime.now()
    return int(
        connection.execute(
            sa.text(
                """
                INSERT INTO sys_menu (
                    name, type, "order", permission, icon, route_name, route_path,
                    component_path, redirect, hidden, keep_alive, always_show, title,
                    params, affix, client, parent_id, uuid, status, description,
                    created_time, updated_time, is_deleted, deleted_time
                ) VALUES (
                    '预算管理', 1, 5, NULL, 'ri:funds-line', 'Budget', '/budget',
                    NULL, '/budget/budget-detail', false, true, false, '预算管理',
                    NULL, false, 'pc', NULL, :uuid, '0', '预算模块迁移',
                    :created_time, :updated_time, false, NULL
                ) RETURNING id
                """
            ),
            {
                "uuid": str(uuid4()),
                "created_time": now,
                "updated_time": now,
            },
        ).scalar_one()
    )


def upgrade() -> None:
    connection = op.get_bind()
    has_menus = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM sys_menu LIMIT 1)")
    ).scalar_one()
    if not has_menus:
        return

    budget_root_id = _insert_budget_root(connection)
    budget_page_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE route_name = 'BudgetDetail' AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    if budget_page_id is None:
        return

    connection.execute(
        sa.text(
            """
            UPDATE sys_menu
            SET parent_id = :parent_id,
                permission = 'module_budget:budget_detail:query',
                component_path = 'module_budget/budget_detail/index',
                updated_time = :updated_time
            WHERE id = :menu_id
            """
        ),
        {
            "parent_id": budget_root_id,
            "menu_id": int(budget_page_id),
            "updated_time": datetime.now(),
        },
    )
    connection.execute(
        sa.text(
            """
            UPDATE sys_menu
            SET permission = REPLACE(permission, 'module_financial:budget_detail:',
                                     'module_budget:budget_detail:'),
                updated_time = :updated_time
            WHERE permission LIKE 'module_financial:budget_detail:%'
            """
        ),
        {"updated_time": datetime.now()},
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO sys_role_menus (role_id, menu_id)
            SELECT DISTINCT role_id, :budget_root_id
            FROM sys_role_menus
            WHERE menu_id = :budget_page_id
            ON CONFLICT (role_id, menu_id) DO NOTHING
            """
        ),
        {"budget_root_id": budget_root_id, "budget_page_id": int(budget_page_id)},
    )


def downgrade() -> None:
    connection = op.get_bind()
    budget_root_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE route_name = 'Budget' AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    financial_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE route_name = 'Financial' AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    budget_page_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE route_name = 'BudgetDetail' AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    if financial_id is not None and budget_page_id is not None:
        connection.execute(
            sa.text(
                """
                UPDATE sys_menu
                SET parent_id = :parent_id,
                    permission = 'module_financial:budget_detail:query',
                    component_path = 'module_financial/budget_detail/index',
                    updated_time = :updated_time
                WHERE id = :menu_id
                """
            ),
            {
                "parent_id": int(financial_id),
                "menu_id": int(budget_page_id),
                "updated_time": datetime.now(),
            },
        )
        connection.execute(
            sa.text(
                """
                UPDATE sys_menu
                SET permission = REPLACE(permission, 'module_budget:budget_detail:',
                                         'module_financial:budget_detail:'),
                    updated_time = :updated_time
                WHERE permission LIKE 'module_budget:budget_detail:%'
                """
            ),
            {"updated_time": datetime.now()},
        )
    if budget_root_id is not None:
        connection.execute(
            sa.text("DELETE FROM sys_role_menus WHERE menu_id = :menu_id"),
            {"menu_id": int(budget_root_id)},
        )
        connection.execute(
            sa.text("DELETE FROM sys_menu WHERE id = :menu_id"),
            {"menu_id": int(budget_root_id)},
        )
