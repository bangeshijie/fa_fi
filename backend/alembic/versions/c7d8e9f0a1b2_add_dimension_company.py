"""add company master data

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-11-03
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _insert_missing_dimension_menus() -> None:
    """为已存在的数据库补齐公司主数据菜单。

    新数据库的 sys_menu 表在迁移时仍为空，后续初始化会读取完整的
    sys_menu.json；只有已有业务数据的数据库才在这里增量补菜单。
    """
    connection = op.get_bind()
    menu_count = connection.execute(sa.text("SELECT COUNT(1) FROM sys_menu")).scalar_one()
    if not menu_count:
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
        redirect: str | None,
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
                        :component_path, :redirect, false, true, false, :title,
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
                    "redirect": redirect,
                    "title": name,
                    "parent_id": parent_id,
                    "uuid": str(uuid4()),
                    "created_time": now,
                    "updated_time": now,
                },
            ).scalar_one()
        )

    root_id = insert_menu(
        name="主数据管理",
        menu_type=1,
        order=3,
        permission=None,
        icon="ri:database-2-line",
        route_name="Dimension",
        route_path="/dimension",
        component_path=None,
        redirect="/dimension/company",
        parent_id=None,
    )
    company_id = insert_menu(
        name="公司管理",
        menu_type=2,
        order=1,
        permission="module_dimension:company:query",
        icon="ri:building-line",
        route_name="Company",
        route_path="company",
        component_path="module_dimension/company/index",
        redirect=None,
        parent_id=root_id,
    )

    buttons = [
        ("创建公司", "module_dimension:company:create", 1),
        ("修改公司", "module_dimension:company:update", 2),
        ("删除公司", "module_dimension:company:delete", 3),
        ("批量修改公司状态", "module_dimension:company:patch", 4),
        ("导出公司", "module_dimension:company:export", 5),
        ("详情公司", "module_dimension:company:detail", 6),
        ("查询公司", "module_dimension:company:query", 7),
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
            redirect=None,
            parent_id=company_id,
        )


def upgrade() -> None:
    op.create_table(
        "dim_company",
        sa.Column("code", sa.String(length=32), nullable=False, comment="公司代码"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="公司名称"),
        sa.Column("holding_company_id", sa.Integer(), nullable=True, comment="上级控股公司ID"),
        sa.Column("address", sa.String(length=255), nullable=True, comment="公司地址"),
        sa.Column("phone", sa.String(length=32), nullable=True, comment="公司电话"),
        sa.Column(
            "business_license_no",
            sa.String(length=64),
            nullable=True,
            comment="营业执照号码",
        ),
        sa.Column("leader", sa.String(length=64), nullable=True, comment="公司负责人"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
        sa.Column("uuid", sa.String(length=64), nullable=False, comment="UUID全局唯一标识"),
        sa.Column("status", sa.String(length=10), nullable=False, comment="状态(0:正常 1:禁用)"),
        sa.Column("description", sa.Text(), nullable=True, comment="备注/描述"),
        sa.Column("created_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_time", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, comment="是否已删除(0:未删除 1:已删除)"),
        sa.Column("deleted_time", sa.DateTime(), nullable=True, comment="删除时间"),
        sa.Column("created_id", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("updated_id", sa.Integer(), nullable=True, comment="更新人ID"),
        sa.Column("deleted_id", sa.Integer(), nullable=True, comment="删除人ID"),
        sa.ForeignKeyConstraint(["created_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["holding_company_id"],
            ["dim_company.id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_dim_company_code"),
        sa.UniqueConstraint("name", name="uq_dim_company_name"),
        sa.UniqueConstraint("business_license_no", name="uq_dim_company_license_no"),
        comment="公司主数据表",
    )
    for column in (
        "created_id",
        "holding_company_id",
        "created_time",
        "deleted_id",
        "deleted_time",
        "id",
        "is_deleted",
        "status",
        "updated_id",
        "updated_time",
    ):
        op.create_index(f"ix_dim_company_{column}", "dim_company", [column], unique=False)
    op.create_index("ix_dim_company_uuid", "dim_company", ["uuid"], unique=True)

    _insert_missing_dimension_menus()


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sys_menu WHERE permission LIKE 'module_dimension:company:%' "
            "OR route_name IN ('Company', 'Dimension')"
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
        "holding_company_id",
        "created_time",
        "created_id",
    ):
        op.drop_index(f"ix_dim_company_{column}", table_name="dim_company")
    op.drop_table("dim_company")
