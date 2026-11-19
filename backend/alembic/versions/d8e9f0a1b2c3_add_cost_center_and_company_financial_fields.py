"""add company financial fields and cost center master data

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-11-03
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _insert_missing_cost_center_menus() -> None:
    """为已存在的数据库补齐成本中心菜单。"""

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

    cost_center_id = insert_menu(
        name="成本中心管理",
        menu_type=2,
        order=2,
        permission="module_dimension:cost_center:query",
        icon="ri:focus-3-line",
        route_name="CostCenter",
        route_path="cost-center",
        component_path="module_dimension/cost_center/index",
        parent_id=int(root_id),
    )

    buttons = [
        ("创建成本中心", "module_dimension:cost_center:create", 1),
        ("修改成本中心", "module_dimension:cost_center:update", 2),
        ("删除成本中心", "module_dimension:cost_center:delete", 3),
        ("修改成本中心状态", "module_dimension:cost_center:patch", 4),
        ("导出成本中心", "module_dimension:cost_center:export", 5),
        ("导入成本中心", "module_dimension:cost_center:import", 6),
        ("下载成本中心模板", "module_dimension:cost_center:download", 7),
        ("详情成本中心", "module_dimension:cost_center:detail", 8),
        ("查询成本中心", "module_dimension:cost_center:query", 9),
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
            parent_id=cost_center_id,
        )


def upgrade() -> None:
    op.add_column(
        "dim_company",
        sa.Column("holding_ratio", sa.Numeric(precision=5, scale=2), nullable=True, comment="控股比例(%)"),
    )
    op.add_column(
        "dim_company",
        sa.Column(
            "registered_capital",
            sa.Numeric(precision=18, scale=2),
            nullable=True,
            comment="注册资本(万元)",
        ),
    )

    op.create_table(
        "dim_cost_center",
        sa.Column("code", sa.String(length=32), nullable=False, comment="成本中心代码"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="成本中心名称"),
        sa.Column("company_id", sa.Integer(), nullable=False, comment="所属公司ID"),
        sa.Column("function_scope", sa.String(length=4), nullable=False, comment="职能范围(4位数字)"),
        sa.Column("dept_id", sa.Integer(), nullable=False, comment="所属组织部门ID"),
        sa.Column("leader", sa.String(length=64), nullable=True, comment="成本中心负责人"),
        sa.Column("enable_time", sa.DateTime(), nullable=False, comment="启用时间"),
        sa.Column(
            "is_frozen",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="是否冻结(0:否 1:是)",
        ),
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
        sa.ForeignKeyConstraint(
            ["company_id"], ["dim_company.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["dept_id"], ["sys_dept.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
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
        sa.UniqueConstraint("code", name="uq_dim_cost_center_code"),
        comment="成本中心主数据表",
    )
    for column in (
        "company_id",
        "created_id",
        "dept_id",
        "enable_time",
        "id",
        "is_deleted",
        "is_frozen",
        "status",
        "updated_time",
    ):
        op.create_index(f"ix_dim_cost_center_{column}", "dim_cost_center", [column], unique=False)
    op.create_index("ix_dim_cost_center_uuid", "dim_cost_center", ["uuid"], unique=True)

    _insert_missing_cost_center_menus()


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sys_menu WHERE permission LIKE 'module_dimension:cost_center:%' "
            "OR route_name = 'CostCenter'"
        )
    )
    for column in (
        "uuid",
        "updated_time",
        "status",
        "is_deleted",
        "id",
        "is_frozen",
        "enable_time",
        "dept_id",
        "deleted_time",
        "deleted_id",
        "created_time",
        "created_id",
        "company_id",
    ):
        op.drop_index(f"ix_dim_cost_center_{column}", table_name="dim_cost_center")
    op.drop_table("dim_cost_center")
    op.drop_column("dim_company", "registered_capital")
    op.drop_column("dim_company", "holding_ratio")
