from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.request import PageResultSchema
from app.core.base_schema import BaseSchema, UserBySchema


VoucherDataSourceCategory = Literal["SAP原始明细", "单体财报调整", "合并财报调整", "管理调整"]
VoucherDebitCreditDirection = Literal["借", "贷"]


def _normalize_ids(values: list[int] | None, single_value: int | None = None) -> list[int]:
    candidates = list(values or [])
    if single_value is not None:
        candidates.append(single_value)
    return sorted({int(item) for item in candidates if int(item) > 0})


class AccountingVoucherDetailCreateSchema(BaseModel):
    """会计凭证明细创建/更新模型。"""

    year: int = Field(..., ge=1900, le=2999, description="年度")
    company_id: int = Field(..., gt=0, description="公司ID")
    voucher_number: str = Field(..., min_length=1, max_length=64, description="会计凭证号")
    line_number: str = Field(..., min_length=1, max_length=20, description="行号")
    accounting_subject_id: int = Field(..., gt=0, description="会计科目ID")
    cost_center_id: int | None = Field(default=None, gt=0, description="成本中心ID")
    belonging_month: int | None = Field(default=None, ge=1, le=12, description="归属月份")
    posting_date: date = Field(..., description="过账日期")
    currency: str = Field(default="RMB", min_length=1, max_length=16, description="币种")
    amount: Decimal = Field(..., max_digits=18, decimal_places=2, description="金额")
    debit_credit_direction: VoucherDebitCreditDirection = Field(..., description="借贷方向")
    voucher_text: str | None = Field(default=None, max_length=500, description="凭证文本")
    data_source_category: VoucherDataSourceCategory = Field(
        default="SAP原始明细", description="数据来源分类"
    )
    source_description: str | None = Field(default=None, max_length=2000, description="数据来源说明")

    @field_validator("voucher_number", "line_number", mode="before")
    @classmethod
    def normalize_key_text(cls, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise ValueError("凭证号和行号不能为空")
        return value

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = str(value or "").strip().upper()
        if not value:
            raise ValueError("币种不能为空")
        return value

    @field_validator("voucher_text", "source_description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @model_validator(mode="after")
    def default_belonging_month(self):
        if self.belonging_month is None:
            self.belonging_month = self.posting_date.month
        return self


class AccountingVoucherDetailUpdateSchema(AccountingVoucherDetailCreateSchema):
    """会计凭证明细更新模型。"""


class AccountingVoucherDetailOutSchema(
    AccountingVoucherDetailCreateSchema, BaseSchema, UserBySchema
):
    """会计凭证明细响应模型。"""

    company_code: str | None = None
    company_name: str | None = None
    accounting_subject_code: str | None = None
    accounting_subject_name: str | None = None
    cost_center_code: str | None = None
    cost_center_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AccountingVoucherDetailImportErrorSchema(BaseModel):
    """会计凭证明细导入单行错误。"""

    row_number: int = Field(..., description="Excel行号")
    voucher_number: str | None = Field(default=None, description="会计凭证号")
    line_number: str | None = Field(default=None, description="行号")
    reason: str = Field(..., description="失败原因")


class AccountingVoucherDetailImportResultSchema(BaseModel):
    """会计凭证明细导入批次结果。"""

    total_count: int = Field(default=0, description="数据总行数")
    success_count: int = Field(default=0, description="成功处理行数")
    created_count: int = Field(default=0, description="新增会计凭证明细数")
    updated_count: int = Field(default=0, description="更新会计凭证明细数")
    duplicate_count: int = Field(default=0, description="已存在业务键数")
    failed_count: int = Field(default=0, description="失败行数")
    errors: list[AccountingVoucherDetailImportErrorSchema] = Field(
        default_factory=list, description="失败明细"
    )
    errors_truncated: bool = Field(default=False, description="失败明细是否已截断")


class AccountingVoucherDetailPageSchema(PageResultSchema):
    items: list[AccountingVoucherDetailOutSchema] = Field(default_factory=list)
    amount_sum: Decimal = Field(default=Decimal("0.00"), description="当前筛选条件下的金额汇总")


class AccountingVoucherDetailQueryParam:
    def __init__(
        self,
        year: int | None = Query(None, description="年度"),
        company_id: int | None = Query(None, description="公司"),
        voucher_number: str | None = Query(None, description="会计凭证号"),
        accounting_subject_id: int | None = Query(None, description="会计科目"),
        accounting_subject_ids: list[int] | None = Query(None, description="会计科目，可多选"),
        cost_center_id: int | None = Query(None, description="成本中心"),
        cost_center_ids: list[int] | None = Query(None, description="成本中心，可多选"),
        department_ids: list[int] | None = Query(None, description="部门，可多选并包含下级"),
        belonging_month: int | None = Query(None, ge=1, le=12, description="月份（兼容单值查询）"),
        belonging_months: list[Annotated[int, Field(ge=1, le=12)]] | None = Query(
            None, description="月份，可多选"
        ),
        data_source_category: list[str] | None = Query(None, description="数据来源分类（可多选）"),
        posting_date: list[date] | None = Query(None, description="过账日期范围"),
    ) -> None:
        if year is not None:
            self.year = ("eq", year)
        if company_id is not None:
            self.company_id = ("eq", company_id)
        if voucher_number and voucher_number.strip():
            self.voucher_number = ("like", voucher_number.strip())
        subject_ids = _normalize_ids(accounting_subject_ids, accounting_subject_id)
        if subject_ids:
            self.accounting_subject_id = ("in", subject_ids)
        cost_center_values = _normalize_ids(cost_center_ids, cost_center_id)
        if cost_center_values:
            self.cost_center_id = ("in", cost_center_values)
        if department_ids:
            self.department_ids = _normalize_ids(department_ids)
        selected_months = sorted(
            {*(belonging_months or []), *([belonging_month] if belonging_month is not None else [])}
        )
        if selected_months:
            self.belonging_month = ("in", selected_months)
        if data_source_category:
            categories = [item.strip() for item in data_source_category if item.strip()]
            if categories:
                self.data_source_category = ("in", categories)
        if posting_date and len(posting_date) == 2:
            self.posting_date = ("between", posting_date)
