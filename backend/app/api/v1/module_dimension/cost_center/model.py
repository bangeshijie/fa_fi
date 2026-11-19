from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import PermissionFilterStrategy
from app.core.base_model import ModelMixin, UserMixin

if TYPE_CHECKING:
    from app.api.v1.module_dimension.company.model import CompanyModel
    from app.api.v1.module_system.dept.model import DeptModel


class CostCenterModel(ModelMixin, UserMixin):
    """成本中心主数据模型。"""

    __tablename__: str = "dim_cost_center"
    __table_args__ = (
        UniqueConstraint("code", name="uq_dim_cost_center_code"),
        {"comment": "成本中心主数据表"},
    )
    __loader_options__: list[str] = [
        "created_by",
        "updated_by",
        "deleted_by",
        "company",
        "department",
    ]
    __permission_strategy__: PermissionFilterStrategy = PermissionFilterStrategy.MASTER_DATA

    code: Mapped[str] = mapped_column(String(32), nullable=False, comment="成本中心代码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="成本中心名称")
    company_id: Mapped[int] = mapped_column(
        ForeignKey("dim_company.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="所属公司ID",
    )
    function_scope: Mapped[str] = mapped_column(
        String(4), nullable=False, comment="职能范围(4位数字)"
    )
    dept_id: Mapped[int] = mapped_column(
        ForeignKey("sys_dept.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="所属组织部门ID",
    )
    leader: Mapped[str | None] = mapped_column(String(64), default=None, comment="成本中心负责人")
    enable_time: Mapped[date] = mapped_column(Date, nullable=False, comment="启用日期")

    company: Mapped["CompanyModel"] = relationship(
        "CompanyModel", foreign_keys=[company_id], lazy="selectin"
    )
    department: Mapped["DeptModel"] = relationship(
        "DeptModel", foreign_keys=[dept_id], lazy="selectin"
    )

    @property
    def company_code(self) -> str | None:
        return self.company.code if self.company else None

    @property
    def company_name(self) -> str | None:
        return self.company.name if self.company else None

    @property
    def dept_code(self) -> str | None:
        return self.department.code if self.department else None

    @property
    def dept_name(self) -> str | None:
        return self.department.name if self.department else None
