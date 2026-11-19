from typing import ClassVar

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import PermissionFilterStrategy
from app.core.base_model import ModelMixin, UserMixin


class AccountingSubjectModel(ModelMixin, UserMixin):
    """会计科目主数据模型。"""

    __tablename__: str = "dim_accounting_subject"
    __table_args__ = (
        UniqueConstraint("code", name="uq_dim_accounting_subject_code"),
        {"comment": "会计科目主数据表"},
    )
    __loader_options__: ClassVar[list[str]] = ["created_by", "updated_by", "deleted_by"]
    __permission_strategy__: PermissionFilterStrategy = (
        PermissionFilterStrategy.MASTER_DATA
    )

    code: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="会计科目代码"
    )
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="会计科目名称"
    )
    balance_direction: Mapped[str] = mapped_column(
        String(2), nullable=False, comment="科目余额方向(借/贷)"
    )
    accounting_statement_subject: Mapped[str | None] = mapped_column(
        String(128), default=None, comment="所属会计报表科目"
    )
    management_category_level3: Mapped[str | None] = mapped_column(
        String(128), default=None, comment="管理科目三级分类"
    )
    management_category_level1: Mapped[str | None] = mapped_column(
        String(64), default=None, comment="管理科目一级分类"
    )
    management_category_level2: Mapped[str | None] = mapped_column(
        String(64), default=None, comment="管理科目二级分类"
    )
    leader: Mapped[str | None] = mapped_column(
        String(64), default=None, comment="科目负责人"
    )
