"""add financial voucher and budget detail tables

Revision ID: i2j3k4l5m6n7
Revises: h1b2c3d4e5f6
Create Date: 2026-11-09
"""

from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "i2j3k4l5m6n7"
down_revision: Union[str, Sequence[str], None] = "h1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _insert_missing_financial_menus() -> None:
    """为已存在的数据库补齐财务模块菜单和按钮权限。"""

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
        lookup = "route_name = :route_name" if route_name else "permission = :permission"
        params = {"route_name": route_name, "permission": permission}
        existing = connection.execute(
            sa.text(
                f"SELECT id FROM sys_menu WHERE {lookup} AND is_deleted = false LIMIT 1"
            ),
            params,
        ).scalar_one_or_none()
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
                        NULL, false, 'pc', :parent_id, :uuid, '0', '财务模块初始化',
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

    financial_id = insert_menu(
        name="财务管理",
        menu_type=1,
        order=4,
        permission=None,
        icon="ri:funds-box-line",
        route_name="Financial",
        route_path="/financial",
        component_path=None,
        redirect="/financial/accounting-voucher-detail",
        parent_id=None,
    )
    voucher_id = insert_menu(
        name="会计凭证明细",
        menu_type=2,
        order=1,
        permission="module_financial:accounting_voucher_detail:query",
        icon="ri:file-list-3-line",
        route_name="AccountingVoucherDetail",
        route_path="accounting-voucher-detail",
        component_path="module_financial/accounting_voucher_detail/index",
        redirect=None,
        parent_id=financial_id,
    )
    budget_id = insert_menu(
        name="预算明细",
        menu_type=2,
        order=2,
        permission="module_financial:budget_detail:query",
        icon="ri:funds-line",
        route_name="BudgetDetail",
        route_path="budget-detail",
        component_path="module_financial/budget_detail/index",
        redirect=None,
        parent_id=financial_id,
    )
    for parent_id, buttons in (
        (
            voucher_id,
            [
                ("创建会计凭证明细", "module_financial:accounting_voucher_detail:create"),
                ("修改会计凭证明细", "module_financial:accounting_voucher_detail:update"),
                ("删除会计凭证明细", "module_financial:accounting_voucher_detail:delete"),
                ("详情会计凭证明细", "module_financial:accounting_voucher_detail:detail"),
                ("导出会计凭证明细", "module_financial:accounting_voucher_detail:export"),
                ("导入会计凭证明细", "module_financial:accounting_voucher_detail:import"),
                ("下载会计凭证明细模板", "module_financial:accounting_voucher_detail:download"),
                ("查询会计凭证明细", "module_financial:accounting_voucher_detail:query"),
            ],
        ),
        (
            budget_id,
            [
                ("创建预算明细", "module_financial:budget_detail:create"),
                ("修改预算明细", "module_financial:budget_detail:update"),
                ("删除预算明细", "module_financial:budget_detail:delete"),
                ("详情预算明细", "module_financial:budget_detail:detail"),
                ("导出预算明细", "module_financial:budget_detail:export"),
                ("导入预算明细", "module_financial:budget_detail:import"),
                ("下载预算明细模板", "module_financial:budget_detail:download"),
                ("查询预算明细", "module_financial:budget_detail:query"),
            ],
        ),
    ):
        for button_order, (button_name, permission) in enumerate(buttons, start=1):
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
                parent_id=parent_id,
            )


def upgrade() -> None:
    op.create_table(
        "fin_accounting_voucher_detail",
        sa.Column("year", sa.SmallInteger(), nullable=False, comment="年度"),
        sa.Column("company_id", sa.Integer(), nullable=False, comment="公司ID（公司代码关联）"),
        sa.Column("voucher_number", sa.String(length=64), nullable=False, comment="会计凭证号"),
        sa.Column("line_number", sa.String(length=20), nullable=False, comment="行号"),
        sa.Column("accounting_subject_id", sa.Integer(), nullable=False, comment="会计科目ID"),
        sa.Column("cost_center_id", sa.Integer(), nullable=True, comment="成本中心ID"),
        sa.Column("belonging_month", sa.SmallInteger(), nullable=False, comment="归属月份(1-12)"),
        sa.Column("posting_date", sa.Date(), nullable=False, comment="过账日期"),
        sa.Column("data_source_category", sa.String(length=32), nullable=False, comment="数据来源分类"),
        sa.Column("source_description", sa.Text(), nullable=True, comment="数据来源说明"),
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
        sa.CheckConstraint("belonging_month BETWEEN 1 AND 12", name="ck_fin_voucher_detail_month"),
        sa.CheckConstraint(
            "data_source_category IN ('SAP原始明细', '单体财报调整', '合并财报调整', '管理调整')",
            name="ck_fin_voucher_detail_source_category",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["dim_company.id"], onupdate="CASCADE", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["accounting_subject_id"], ["dim_accounting_subject.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["cost_center_id"], ["dim_cost_center.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "company_id", "voucher_number", "line_number", name="uq_fin_voucher_detail_business_key"),
        comment="会计凭证明细表",
    )
    op.create_table(
        "fin_budget_detail",
        sa.Column("budget_version", sa.String(length=64), nullable=False, comment="预算版本"),
        sa.Column("year", sa.SmallInteger(), nullable=False, comment="年度"),
        sa.Column("company_id", sa.Integer(), nullable=False, comment="公司ID（公司代码关联）"),
        sa.Column("accounting_subject_id", sa.Integer(), nullable=False, comment="会计科目ID"),
        sa.Column("cost_center_id", sa.Integer(), nullable=True, comment="成本中心ID"),
        sa.Column("belonging_month", sa.SmallInteger(), nullable=False, comment="归属月份(1-12)"),
        sa.Column("data_source_category", sa.String(length=16), nullable=False, comment="数据来源分类"),
        sa.Column("data_source", sa.String(length=128), nullable=True, comment="数据来源"),
        sa.Column("source_description", sa.Text(), nullable=True, comment="数据来源说明"),
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
        sa.CheckConstraint("belonging_month BETWEEN 1 AND 12", name="ck_fin_budget_detail_month"),
        sa.CheckConstraint("data_source_category IN ('原始', '调整')", name="ck_fin_budget_detail_source_category"),
        sa.ForeignKeyConstraint(["company_id"], ["dim_company.id"], onupdate="CASCADE", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["accounting_subject_id"], ["dim_accounting_subject.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["cost_center_id"], ["dim_cost_center.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("budget_version", name="uq_fin_budget_detail_version"),
        comment="预算明细表",
    )

    for table, columns in {
        "fin_accounting_voucher_detail": (
            "accounting_subject_id",
            "belonging_month",
            "company_id",
            "cost_center_id",
            "created_id",
            "created_time",
            "deleted_id",
            "deleted_time",
            "id",
            "is_deleted",
            "posting_date",
            "status",
            "updated_id",
            "updated_time",
            "year",
        ),
        "fin_budget_detail": (
            "accounting_subject_id",
            "belonging_month",
            "company_id",
            "cost_center_id",
            "created_id",
            "created_time",
            "deleted_id",
            "deleted_time",
            "id",
            "is_deleted",
            "status",
            "updated_id",
            "updated_time",
            "year",
        ),
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column], unique=False)
        op.create_index(f"ix_{table}_uuid", table, ["uuid"], unique=True)

    _insert_missing_financial_menus()


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM sys_menu WHERE permission LIKE 'module_financial:%' "
            "OR route_name IN ('Financial', 'AccountingVoucherDetail', 'BudgetDetail')"
        )
    )
    for table, columns in {
        "fin_accounting_voucher_detail": (
            "accounting_subject_id", "belonging_month", "company_id", "cost_center_id",
            "created_id", "created_time", "deleted_id", "deleted_time", "id", "is_deleted",
            "posting_date", "status", "updated_id", "updated_time", "year", "uuid",
        ),
        "fin_budget_detail": (
            "accounting_subject_id", "belonging_month", "company_id", "cost_center_id",
            "created_id", "created_time", "deleted_id", "deleted_time", "id", "is_deleted",
            "status", "updated_id", "updated_time", "year", "uuid",
        ),
    }.items():
        for column in columns:
            op.drop_index(f"ix_{table}_{column}", table_name=table, if_exists=True)
    op.drop_table("fin_budget_detail")
    op.drop_table("fin_accounting_voucher_detail")
