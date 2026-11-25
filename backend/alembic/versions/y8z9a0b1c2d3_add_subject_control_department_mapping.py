"""add subject control department mapping and remove accounting subject leader

Revision ID: y8z9a0b1c2d3
Revises: x7y8z9a0b1c2
Create Date: 2026-11-20
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "y8z9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "x7y8z9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSION_PREFIX = "module_dimension:subject_control_department_mapping"


def _insert_mapping_menus() -> None:
    connection = op.get_bind()
    root_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu "
            "WHERE route_name = 'Dimension' AND is_deleted = false LIMIT 1"
        )
    ).scalar_one_or_none()
    if root_id is None:
        return

    now = datetime.now()
    page_permission = f"{PERMISSION_PREFIX}:query"
    page_id = connection.execute(
        sa.text(
            "SELECT id FROM sys_menu WHERE permission = :permission "
            "AND type = 2 AND is_deleted = false LIMIT 1"
        ),
        {"permission": page_permission},
    ).scalar_one_or_none()

    if page_id is None:
        page_id = connection.execute(
            sa.text(
                """
                INSERT INTO sys_menu (
                    name, type, "order", permission, icon, route_name, route_path,
                    component_path, redirect, hidden, keep_alive, always_show, title,
                    params, affix, client, parent_id, uuid, status, description,
                    created_time, updated_time, is_deleted, deleted_time
                ) VALUES (
                    '科目主控部门映射', 2, 4, :permission, 'ri:git-merge-line',
                    'SubjectControlDepartmentMapping', 'subject-control-department-mapping',
                    'module_dimension/subject_control_department_mapping/index', NULL,
                    false, true, false, '科目主控部门映射', NULL, false, 'pc', :parent_id,
                    :uuid, '0', '主数据模块初始化', :created_time, :updated_time, false, NULL
                ) RETURNING id
                """
            ),
            {
                "permission": page_permission,
                "parent_id": int(root_id),
                "uuid": str(uuid4()),
                "created_time": now,
                "updated_time": now,
            },
        ).scalar_one()

    buttons = [
        ("创建科目主控部门映射", f"{PERMISSION_PREFIX}:create", 1),
        ("修改科目主控部门映射", f"{PERMISSION_PREFIX}:update", 2),
        ("删除科目主控部门映射", f"{PERMISSION_PREFIX}:delete", 3),
        ("修改科目主控部门映射状态", f"{PERMISSION_PREFIX}:patch", 4),
        ("详情科目主控部门映射", f"{PERMISSION_PREFIX}:detail", 5),
        ("查询科目主控部门映射", f"{PERMISSION_PREFIX}:query", 6),
    ]
    for name, permission, order in buttons:
        exists = connection.execute(
            sa.text(
                "SELECT id FROM sys_menu WHERE permission = :permission "
                "AND parent_id = :parent_id AND is_deleted = false LIMIT 1"
            ),
            {"permission": permission, "parent_id": int(page_id)},
        ).scalar_one_or_none()
        if exists:
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
                    :name, 3, :order, :permission, NULL, NULL, NULL, NULL, NULL,
                    false, true, false, :name, NULL, false, 'pc', :parent_id, :uuid,
                    '0', '主数据模块初始化', :created_time, :updated_time, false, NULL
                )
                """
            ),
            {
                "name": name,
                "order": order,
                "permission": permission,
                "parent_id": int(page_id),
                "uuid": str(uuid4()),
                "created_time": now,
                "updated_time": now,
            },
        )


def upgrade() -> None:
    op.drop_column("dim_accounting_subject", "leader")

    op.create_table(
        "dim_subject_control_department_mapping",
        sa.Column(
            "accounting_subject_id",
            sa.Integer(),
            nullable=False,
            comment="会计科目ID",
        ),
        sa.Column("dept_id", sa.Integer(), nullable=False, comment="部门ID"),
        sa.Column(
            "control_department",
            sa.String(length=128),
            nullable=False,
            comment="主控部门",
        ),
        sa.Column(
            "control_person", sa.String(length=64), nullable=False, comment="主控人"
        ),
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
            ["accounting_subject_id"],
            ["dim_accounting_subject.id"],
            onupdate="CASCADE",
            ondelete="RESTRICT",
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
        sa.UniqueConstraint(
            "accounting_subject_id",
            "dept_id",
            name="uq_dim_subject_control_mapping_subject_dept",
        ),
        comment="科目主控部门映射表",
    )
    for column in (
        "accounting_subject_id",
        "created_id",
        "created_time",
        "deleted_id",
        "deleted_time",
        "dept_id",
        "id",
        "is_deleted",
        "status",
        "updated_id",
        "updated_time",
    ):
        op.create_index(
            f"ix_dim_subject_control_department_mapping_{column}",
            "dim_subject_control_department_mapping",
            [column],
            unique=False,
        )
    op.create_index(
        "ix_dim_subject_control_department_mapping_uuid",
        "dim_subject_control_department_mapping",
        ["uuid"],
        unique=True,
    )

    _insert_mapping_menus()


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sys_menu WHERE permission LIKE :prefix "
            "OR route_name = 'SubjectControlDepartmentMapping'"
        ),
        {"prefix": f"{PERMISSION_PREFIX}:%"},
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
        "dept_id",
        "accounting_subject_id",
    ):
        op.drop_index(
            f"ix_dim_subject_control_department_mapping_{column}",
            table_name="dim_subject_control_department_mapping",
        )
    op.drop_index(
        "ix_dim_subject_control_department_mapping_uuid",
        table_name="dim_subject_control_department_mapping",
    )
    op.drop_table("dim_subject_control_department_mapping")
    op.add_column(
        "dim_accounting_subject",
        sa.Column("leader", sa.String(length=64), nullable=True, comment="科目负责人"),
    )
