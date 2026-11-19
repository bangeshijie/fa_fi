from decimal import Decimal

from app.common.enums import PermissionFilterStrategy
from app.core.base_model import ModelMixin, UserMixin
from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class CompanyModel(ModelMixin, UserMixin):
    """公司主数据模型。"""

    __tablename__: str = "dim_company"
    __table_args__ = (
        UniqueConstraint("code", name="uq_dim_company_code"),
        UniqueConstraint("name", name="uq_dim_company_name"),
        UniqueConstraint("business_license_no", name="uq_dim_company_license_no"),
        {"comment": "公司主数据表"},
    )
    __loader_options__: list[str] = ["created_by", "updated_by", "deleted_by"]
    # 公司主数据不按创建人或部门切分，是否可操作由接口权限控制。
    __permission_strategy__: PermissionFilterStrategy = PermissionFilterStrategy.MASTER_DATA

    code: Mapped[str] = mapped_column(String(32), nullable=False, comment="公司代码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="公司名称")
    holding_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("dim_company.id", ondelete="SET NULL", onupdate="CASCADE"),
        default=None,
        index=True,
        comment="上级控股公司ID",
    )
    address: Mapped[str | None] = mapped_column(String(255), default=None, comment="公司地址")
    phone: Mapped[str | None] = mapped_column(String(32), default=None, comment="公司电话")
    business_license_no: Mapped[str | None] = mapped_column(
        String(64), default=None, comment="营业执照号码"
    )
    leader: Mapped[str | None] = mapped_column(String(64), default=None, comment="公司负责人")
    holding_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), default=None, comment="控股比例(%)"
    )
    registered_capital: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), default=None, comment="注册资本(万元)"
    )

    holding_company: Mapped["CompanyModel | None"] = relationship(
        "CompanyModel",
        back_populates="subsidiaries",
        remote_side="CompanyModel.id",
        foreign_keys=[holding_company_id],
        uselist=False,
        lazy="selectin",
    )
    subsidiaries: Mapped[list["CompanyModel"]] = relationship(
        "CompanyModel",
        back_populates="holding_company",
        foreign_keys=[holding_company_id],
        lazy="selectin",
    )

    @property
    def holding_company_code(self) -> str | None:
        return self.holding_company.code if self.holding_company else None

    @property
    def holding_company_name(self) -> str | None:
        return self.holding_company.name if self.holding_company else None
