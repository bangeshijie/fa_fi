"""backfill management finance variance menu to expense analysis roles

Revision ID: x7y8z9a0b1c2
Revises: w6x7y8z9a0b1
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "x7y8z9a0b1c2"
down_revision: Union[str, Sequence[str], None] = "w6x7y8z9a0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_PAGE_PERMISSION = "module_financial:management_finance_variance:query"
SOURCE_PERMISSION = "module_financial:expense_analysis:query"


def upgrade() -> None:
    connection = op.get_bind()
    page_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE permission = :permission AND type = 2 AND is_deleted = false LIMIT 1"
        ),
        {"permission": NEW_PAGE_PERMISSION},
    ).scalar_one_or_none()
    button_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE permission = :permission AND type = 3 AND is_deleted = false LIMIT 1"
        ),
        {"permission": NEW_PAGE_PERMISSION},
    ).scalar_one_or_none()
    if page_id is None or button_id is None:
        return

    connection.execute(
        sa.text(
            """
            INSERT INTO sys_role_menus (role_id, menu_id)
            SELECT DISTINCT role_menus.role_id, :menu_id
            FROM sys_role_menus AS role_menus
            JOIN sys_menu AS source_menu ON source_menu.id = role_menus.menu_id
            WHERE source_menu.permission = :source_permission
            ON CONFLICT (role_id, menu_id) DO NOTHING
            """
        ),
        {
            "menu_id": int(page_id),
            "source_permission": SOURCE_PERMISSION,
        },
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO sys_role_menus (role_id, menu_id)
            SELECT DISTINCT role_menus.role_id, :menu_id
            FROM sys_role_menus AS role_menus
            JOIN sys_menu AS source_menu ON source_menu.id = role_menus.menu_id
            WHERE source_menu.permission = :source_permission
            ON CONFLICT (role_id, menu_id) DO NOTHING
            """
        ),
        {
            "menu_id": int(button_id),
            "source_permission": SOURCE_PERMISSION,
        },
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sys_role_menus "
            "WHERE menu_id IN ("
            "SELECT id FROM sys_menu "
            "WHERE permission = :permission AND is_deleted = false"
            ")"
        ),
        {"permission": NEW_PAGE_PERMISSION},
    )
