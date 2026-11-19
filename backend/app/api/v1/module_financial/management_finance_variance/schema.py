"""管财差异分析接口模型。"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


VoucherDataSourceCategory = Literal[
    "SAP原始明细", "单体财报调整", "合并财报调整", "管理调整"
]

MANAGEMENT_FINANCE_DATA_SOURCE_CATEGORIES: tuple[str, ...] = (
    "SAP原始明细",
    "单体财报调整",
    "合并财报调整",
    "管理调整",
)


class ManagementFinanceVarianceQuerySchema(BaseModel):
    """管报与财报差异分析筛选条件。"""

    year: int = Field(..., ge=1900, le=2999, description="年度")
    month: int = Field(..., ge=1, le=12, description="截至月份")
    company_ids: list[int] = Field(default_factory=list, description="公司ID，可多选")
    department_ids: list[int] = Field(default_factory=list, description="部门ID，可多选")
    function_scopes: list[str] = Field(default_factory=list, description="职能范围，可多选")
    management_category_paths: list[list[str]] = Field(
        default_factory=list, description="管理分类路径，可多选"
    )
    management_data_source_categories: list[VoucherDataSourceCategory] = Field(
        default_factory=list, description="管报实际数据来源分类，可多选；为空表示全部"
    )
    financial_data_source_categories: list[VoucherDataSourceCategory] = Field(
        default_factory=list, description="财报实际数据来源分类，可多选；为空表示全部"
    )

    @field_validator("company_ids", "department_ids", mode="before")
    @classmethod
    def normalize_ids(cls, value: list[int] | None) -> list[int]:
        if not value:
            return []
        return sorted({int(item) for item in value if int(item) > 0})

    @field_validator(
        "management_data_source_categories", "financial_data_source_categories", mode="before"
    )
    @classmethod
    def normalize_data_source_categories(cls, value: list[str] | None) -> list[str]:
        if not value:
            return []
        return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))

    @field_validator("management_category_paths", mode="before")
    @classmethod
    def normalize_category_paths(cls, value: list[list[str]] | None) -> list[list[str]]:
        if not value:
            return []
        paths: list[list[str]] = []
        for path in value:
            if not isinstance(path, list):
                continue
            normalized = [str(item).strip() for item in path if str(item).strip()]
            if 1 <= len(normalized) <= 3:
                paths.append(normalized)
        return paths

    @field_validator("function_scopes", mode="before")
    @classmethod
    def normalize_function_scopes(cls, value: list[str] | None) -> list[str]:
        if not value:
            return []
        return sorted({str(item).strip() for item in value if str(item).strip()})


class ManagementFinanceVarianceRowSchema(BaseModel):
    """按管理分类和会计科目展开的差异行。"""

    id: str
    label: str
    code: str | None = None
    node_type: Literal["category", "accounting_subject"]
    level: int
    current_management_report: Decimal = Decimal("0")
    current_financial_report: Decimal = Decimal("0")
    current_variance: Decimal = Decimal("0")
    ytd_management_report: Decimal = Decimal("0")
    ytd_financial_report: Decimal = Decimal("0")
    ytd_variance: Decimal = Decimal("0")
    children: list["ManagementFinanceVarianceRowSchema"] = Field(default_factory=list)


class ManagementFinanceVarianceDimensionSchema(BaseModel):
    """管财差异分析树形结果。"""

    rows: list[ManagementFinanceVarianceRowSchema] = Field(default_factory=list)
    total: ManagementFinanceVarianceRowSchema


class ManagementFinanceVarianceResponseSchema(BaseModel):
    """管财差异分析完整结果。"""

    currency: str = "RMB"
    amount_unit: str = "元"
    available_data_source_categories: list[str] = Field(default_factory=list)
    subject: ManagementFinanceVarianceDimensionSchema


ManagementFinanceVarianceRowSchema.model_rebuild()
