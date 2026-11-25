from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import PermissionFilterStrategy
from app.core.base_model import ModelMixin, UserMixin

if TYPE_CHECKING:
    from app.api.v1.module_dimension.accounting_subject.model import AccountingSubjectModel
    from app.api.v1.module_system.dept.model import DeptModel


class SubjectControlDepartmentMappingModel(ModelMixin, UserMixin):
    """会计科目与部门的主控部门映射主数据。"""

    __tablename__: str = "dim_subject_control_department_mapping"
    __table_args__ = (
        UniqueConstraint(
            "accounting_subject_id",
            "dept_id",
            name="uq_dim_subject_control_mapping_subject_dept",
        ),
        {"comment": "科目主控部门映射表"},
    )
    __loader_options__: ClassVar[list[str]] = [
        "created_by",
        "updated_by",
        "deleted_by",
        "accounting_subject",
        "department",
    ]
    __permission_strategy__: PermissionFilterStrategy = PermissionFilterStrategy.MASTER_DATA

    accounting_subject_id: Mapped[int] = mapped_column(
        ForeignKey("dim_accounting_subject.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="会计科目ID",
    )
    dept_id: Mapped[int] = mapped_column(
        ForeignKey("sys_dept.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="部门ID",
    )
    control_department: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="主控部门"
    )
    control_person: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="主控人"
    )

    accounting_subject: Mapped["AccountingSubjectModel"] = relationship(
        "AccountingSubjectModel", foreign_keys=[accounting_subject_id], lazy="selectin"
    )
    department: Mapped["DeptModel"] = relationship(
        "DeptModel", foreign_keys=[dept_id], lazy="selectin"
    )

    @property
    def accounting_subject_code(self) -> str | None:
        return self.accounting_subject.code if self.accounting_subject else None

    @property
    def accounting_subject_name(self) -> str | None:
        return self.accounting_subject.name if self.accounting_subject else None

    @property
    def dept_code(self) -> str | None:
        return self.department.code if self.department else None

    @property
    def dept_name(self) -> str | None:
        return self.department.name if self.department else None
