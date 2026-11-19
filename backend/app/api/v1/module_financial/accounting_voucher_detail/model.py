from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, SmallInteger, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import PermissionFilterStrategy
from app.core.base_model import ModelMixin, UserMixin

if TYPE_CHECKING:
    from app.api.v1.module_dimension.accounting_subject.model import AccountingSubjectModel
    from app.api.v1.module_dimension.company.model import CompanyModel
    from app.api.v1.module_dimension.cost_center.model import CostCenterModel


class AccountingVoucherDetailModel(ModelMixin, UserMixin):
    """会计凭证明细业务模型。"""

    __tablename__: str = "fin_accounting_voucher_detail"
    __table_args__ = (
        UniqueConstraint(
            "year",
            "company_id",
            "voucher_number",
            "line_number",
            name="uq_fin_voucher_detail_business_key",
        ),
        CheckConstraint("belonging_month BETWEEN 1 AND 12", name="ck_fin_voucher_detail_month"),
        CheckConstraint(
            "data_source_category IN ('SAP原始明细', '单体财报调整', '合并财报调整', '管理调整')",
            name="ck_fin_voucher_detail_source_category",
        ),
        {"comment": "会计凭证明细表"},
    )
    __loader_options__: ClassVar[list[str]] = [
        "created_by",
        "updated_by",
        "deleted_by",
        "company",
        "accounting_subject",
        "cost_center",
    ]
    __permission_strategy__: PermissionFilterStrategy = PermissionFilterStrategy.COST_CENTER_BASED

    year: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True, comment="年度")
    company_id: Mapped[int] = mapped_column(
        ForeignKey("dim_company.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="公司ID（公司代码关联）",
    )
    voucher_number: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="会计凭证号"
    )
    line_number: Mapped[str] = mapped_column(String(20), nullable=False, comment="行号")
    accounting_subject_id: Mapped[int] = mapped_column(
        ForeignKey("dim_accounting_subject.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="会计科目ID",
    )
    cost_center_id: Mapped[int | None] = mapped_column(
        ForeignKey("dim_cost_center.id", ondelete="RESTRICT", onupdate="CASCADE"),
        default=None,
        index=True,
        comment="成本中心ID",
    )
    belonging_month: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, index=True, comment="归属月份(1-12)"
    )
    posting_date: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="过账日期")
    currency: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="RMB",
        server_default=text("'RMB'"),
        comment="币种",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, comment="金额"
    )
    debit_credit_direction: Mapped[str] = mapped_column(
        String(4), nullable=False, comment="借贷方向"
    )
    voucher_text: Mapped[str | None] = mapped_column(
        Text, default=None, comment="凭证文本"
    )
    data_source_category: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="SAP原始明细",
        server_default=text("'SAP原始明细'"),
        comment="数据来源分类",
    )
    source_description: Mapped[str | None] = mapped_column(
        Text, default=None, comment="数据来源说明"
    )

    company: Mapped["CompanyModel"] = relationship("CompanyModel", lazy="selectin")
    accounting_subject: Mapped["AccountingSubjectModel"] = relationship(
        "AccountingSubjectModel", lazy="selectin"
    )
    cost_center: Mapped["CostCenterModel | None"] = relationship(
        "CostCenterModel", lazy="selectin"
    )

    @property
    def company_code(self) -> str | None:
        return self.company.code if self.company else None

    @property
    def company_name(self) -> str | None:
        return self.company.name if self.company else None

    @property
    def accounting_subject_code(self) -> str | None:
        return self.accounting_subject.code if self.accounting_subject else None

    @property
    def accounting_subject_name(self) -> str | None:
        return self.accounting_subject.name if self.accounting_subject else None

    @property
    def cost_center_code(self) -> str | None:
        return self.cost_center.code if self.cost_center else None

    @property
    def cost_center_name(self) -> str | None:
        return self.cost_center.name if self.cost_center else None
