"""费用分析接口模型。"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


VoucherDataSourceCategory = Literal[
    "SAP原始明细", "单体财报调整", "合并财报调整", "管理调整"
]

EXPENSE_ANALYSIS_DATA_SOURCE_CATEGORIES: tuple[str, ...] = (
    "SAP原始明细",
    "单体财报调整",
    "合并财报调整",
    "管理调整",
)


class ExpenseAnalysisQuerySchema(BaseModel):
    """费用分析筛选条件。"""

    budget_version: str = Field(..., min_length=1, max_length=64, description="预算版本")
    year: int = Field(..., ge=1900, le=2999, description="年度")
    month: int = Field(..., ge=1, le=12, description="截至月份")
    company_ids: list[int] = Field(default_factory=list, description="公司ID，可多选")
    department_ids: list[int] = Field(default_factory=list, description="部门ID，可多选")
    function_scopes: list[str] = Field(default_factory=list, description="职能范围，可多选")
    management_category_paths: list[list[str]] = Field(
        default_factory=list, description="管理分类路径，可多选"
    )
    data_source_categories: list[VoucherDataSourceCategory] = Field(
        default_factory=list, description="实际数据来源分类，可多选；为空表示全部"
    )

    @field_validator("budget_version", mode="before")
    @classmethod
    def normalize_budget_version(cls, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise ValueError("预算版本不能为空")
        return value

    @field_validator("company_ids", "department_ids", mode="before")
    @classmethod
    def normalize_ids(cls, value: list[int] | None) -> list[int]:
        if not value:
            return []
        return sorted({int(item) for item in value if int(item) > 0})

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


class ExpenseAnalysisRowSchema(BaseModel):
    """费用分析层级行。金额均为人民币元，前端负责单位换算。"""

    id: str
    label: str
    code: str | None = None
    node_type: Literal["department", "cost_center", "category", "accounting_subject"]
    level: int
    current_actual: Decimal = Decimal("0")
    current_budget: Decimal = Decimal("0")
    current_variance: Decimal = Decimal("0")
    current_completion_rate: Decimal | None = None
    prior_year_current_completion_rate: Decimal | None = None
    ytd_actual: Decimal = Decimal("0")
    ytd_budget: Decimal = Decimal("0")
    ytd_variance: Decimal = Decimal("0")
    ytd_completion_rate: Decimal | None = None
    prior_year_ytd_completion_rate: Decimal | None = None
    annual_budget: Decimal = Decimal("0")
    annual_completion_rate: Decimal | None = None
    actual_months: list[Decimal] = Field(default_factory=list)
    budget_months: list[Decimal] = Field(default_factory=list)
    children: list["ExpenseAnalysisRowSchema"] = Field(default_factory=list)


class ExpenseAnalysisDimensionSchema(BaseModel):
    """单个分析维度的树形结果。"""

    rows: list[ExpenseAnalysisRowSchema] = Field(default_factory=list)
    total: ExpenseAnalysisRowSchema


class ExpenseAnalysisResponseSchema(BaseModel):
    """费用分析完整结果。"""

    currency: str = "RMB"
    amount_unit: str = "元"
    available_data_source_categories: list[str] = Field(default_factory=list)
    department: ExpenseAnalysisDimensionSchema
    subject: ExpenseAnalysisDimensionSchema


ExpenseAnalysisRowSchema.model_rebuild()
