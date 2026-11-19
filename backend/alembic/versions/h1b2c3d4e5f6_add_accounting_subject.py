"""add accounting subject master data

Revision ID: h1b2c3d4e5f6
Revises: g0a1b2c3d4e5f6
Create Date: 2026-11-03
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "h1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "g0a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _insert_missing_accounting_subject_menus() -> None:
    """为已存在的数据库补齐会计科目菜单和按钮权限。"""

    connection = op.get_bind()
    menu_count = connection.execute(sa.text("SELECT COUNT(1) FROM sys_menu")).scalar_one()
    if not menu_count:
        return

    root_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu WHERE route_name = 'Dimension' "
            "AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    if root_id is None:
        return

    now = datetime.now()

    def insert_menu(
        *,
        name: str,
        menu_type: int,
        order: int,
        permission: str | None,
        icon: str | None,
        route_name: str | None,
        route_path: str | None,
        component_path: str | None,
        parent_id: int | None,
    ) -> int:
        if permission:
            existing = connection.execute(
                sa.text(
                    "SELECT id FROM sys_menu WHERE permission = :permission "
                    "AND parent_id IS NOT DISTINCT FROM :parent_id "
                    "AND is_deleted = false LIMIT 1"
                ),
                {"permission": permission, "parent_id": parent_id},
            ).scalar_one_or_none()
        elif route_name:
            existing = connection.execute(
                sa.text(
                    "SELECT id FROM sys_menu WHERE route_name = :route_name "
                    "AND is_deleted = false LIMIT 1"
                ),
                {"route_name": route_name},
            ).scalar_one_or_none()
        else:
            existing = None

        if existing:
            return int(existing)

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
                        :name, :type, :order, :permission, :icon, :route_name, :route_path,
                        :component_path, NULL, false, true, false, :title,
                        NULL, false, 'pc', :parent_id, :uuid, '0', '主数据模块初始化',
                        :created_time, :updated_time, false, NULL
                    ) RETURNING id
                    """
                ),
                {
                    "name": name,
                    "type": menu_type,
                    "order": order,
                    "permission": permission,
                    "icon": icon,
                    "route_name": route_name,
                    "route_path": route_path,
                    "component_path": component_path,
                    "title": name,
                    "parent_id": parent_id,
                    "uuid": str(uuid4()),
                    "created_time": now,
                    "updated_time": now,
                },
            ).scalar_one()
        )

    subject_id = insert_menu(
        name="会计科目管理",
        menu_type=2,
        order=3,
        permission="module_dimension:accounting_subject:query",
        icon="ri:book-2-line",
        route_name="AccountingSubject",
        route_path="accounting-subject",
        component_path="module_dimension/accounting_subject/index",
        parent_id=int(root_id),
    )

    buttons = [
        ("创建会计科目", "module_dimension:accounting_subject:create", 1),
        ("修改会计科目", "module_dimension:accounting_subject:update", 2),
        ("删除会计科目", "module_dimension:accounting_subject:delete", 3),
        ("修改会计科目状态", "module_dimension:accounting_subject:patch", 4),
        ("导出会计科目", "module_dimension:accounting_subject:export", 5),
        ("导入会计科目", "module_dimension:accounting_subject:import", 6),
        ("下载会计科目模板", "module_dimension:accounting_subject:download", 7),
        ("详情会计科目", "module_dimension:accounting_subject:detail", 8),
        ("查询会计科目", "module_dimension:accounting_subject:query", 9),
    ]
    for button_name, permission, button_order in buttons:
        insert_menu(
            name=button_name,
            menu_type=3,
            order=button_order,
            permission=permission,
            icon=None,
            route_name=None,
            route_path=None,
            component_path=None,
            parent_id=subject_id,
        )


def upgrade() -> None:
    op.create_table(
        "dim_accounting_subject",
        sa.Column("code", sa.String(length=32), nullable=False, comment="会计科目代码"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="会计科目名称"),
        sa.Column(
            "accounting_statement_subject",
            sa.String(length=128),
            nullable=True,
            comment="所属会计报表科目",
        ),
        sa.Column(
            "management_statement_subject",
            sa.String(length=128),
            nullable=True,
            comment="所属管理报表科目",
        ),
        sa.Column(
            "management_category_level1",
            sa.String(length=64),
            nullable=True,
            comment="管理科目一级分类",
        ),
        sa.Column(
            "management_category_level2",
            sa.String(length=64),
            nullable=True,
            comment="管理科目二级分类",
        ),
        sa.Column("leader", sa.String(length=64), nullable=True, comment="科目负责人"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
        sa.Column("uuid", sa.String(length=64), nullable=False, comment="UUID全局唯一标识"),
        sa.Column(
            "status",
            sa.String(length=10),
            nullable=False,
            comment="状态(0:正常 1:禁用)",
        ),
        sa.Column("description", sa.Text(), nullable=True, comment="备注/描述"),
        sa.Column("created_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_time", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            comment="是否已删除(0:未删除 1:已删除)",
        ),
        sa.Column("deleted_time", sa.DateTime(), nullable=True, comment="删除时间"),
        sa.Column("created_id", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("updated_id", sa.Integer(), nullable=True, comment="更新人ID"),
        sa.Column("deleted_id", sa.Integer(), nullable=True, comment="删除人ID"),
        sa.ForeignKeyConstraint(
            ["created_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["updated_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["deleted_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_dim_accounting_subject_code"),
        comment="会计科目主数据表",
    )
    for column in (
        "created_id",
        "created_time",
        "deleted_id",
        "deleted_time",
        "id",
        "is_deleted",
        "status",
        "updated_id",
        "updated_time",
    ):
        op.create_index(
            f"ix_dim_accounting_subject_{column}",
            "dim_accounting_subject",
            [column],
            unique=False,
        )
    op.create_index(
        "ix_dim_accounting_subject_uuid",
        "dim_accounting_subject",
        ["uuid"],
        unique=True,
    )

    _insert_missing_accounting_subject_menus()


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sys_menu "
            "WHERE permission LIKE 'module_dimension:accounting_subject:%' "
            "OR route_name = 'AccountingSubject'"
        )
    )
    for column in (
        "uuid",
        "updated_time",
        "updated_id",
        "status",
        "is_deleted",
        "id",
        "deleted_time",
        "deleted_id",
        "created_time",
        "created_id",
    ):
        op.drop_index(
            f"ix_dim_accounting_subject_{column}",
            table_name="dim_accounting_subject",
        )
    op.drop_table("dim_accounting_subject")
