import json
import re

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import QueueEnum
from app.common.request import PageResultSchema
from app.core.base_schema import BaseSchema, UserBySchema


class AccountingSubjectCreateSchema(BaseModel):
    """会计科目主数据创建模型。"""

    code: str = Field(..., min_length=1, max_length=32, description="会计科目代码")
    name: str = Field(..., min_length=1, max_length=128, description="会计科目名称")
    balance_direction: str = Field(..., description="科目余额方向(借/贷)")
    accounting_statement_subject: str | None = Field(
        default=None, max_length=128, description="所属会计报表科目"
    )
    management_category_level3: str | None = Field(
        default=None, max_length=128, description="管理科目三级分类"
    )
    management_category_level1: str | None = Field(
        default=None, max_length=64, description="管理科目一级分类"
    )
    management_category_level2: str | None = Field(
        default=None, max_length=64, description="管理科目二级分类"
    )
    status: str = Field(default="0", description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=500, description="备注")

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = str(value or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,31}", value):
            raise ValueError("会计科目代码需为1-32位字母、数字、点、下划线或短横线")
        return value

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise ValueError("会计科目名称不能为空")
        return value

    @field_validator("balance_direction", mode="before")
    @classmethod
    def validate_balance_direction(cls, value: str) -> str:
        value = str(value or "").strip()
        if value not in {"借", "贷"}:
            raise ValueError("科目余额方向只能选择借或贷")
        return value

    @field_validator(
        "accounting_statement_subject",
        "management_category_level3",
        "management_category_level1",
        "management_category_level2",
        "description",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class AccountingSubjectUpdateSchema(AccountingSubjectCreateSchema):
    """会计科目主数据更新模型。"""


class AccountingSubjectOutSchema(
    AccountingSubjectCreateSchema, BaseSchema, UserBySchema
):
    """会计科目主数据响应模型。"""

    model_config = ConfigDict(from_attributes=True)


class AccountingSubjectOptionSchema(BaseModel):
    """会计科目下拉选项。"""

    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class AccountingSubjectCategoryOptionSchema(BaseModel):
    """会计科目管理分类级联选项。"""

    value: str
    label: str
    children: list["AccountingSubjectCategoryOptionSchema"] = Field(default_factory=list)


class AccountingSubjectImportErrorSchema(BaseModel):
    """会计科目导入单行错误。"""

    row_number: int = Field(..., description="Excel行号")
    code: str | None = Field(default=None, description="会计科目代码")
    reason: str = Field(..., description="失败原因")


class AccountingSubjectImportResultSchema(BaseModel):
    """会计科目导入批次结果。"""

    total_count: int = Field(default=0, description="数据总行数")
    success_count: int = Field(default=0, description="成功处理行数")
    created_count: int = Field(default=0, description="新增会计科目数")
    updated_count: int = Field(default=0, description="更新会计科目数")
    duplicate_count: int = Field(default=0, description="已存在代码数")
    failed_count: int = Field(default=0, description="失败行数")
    errors: list[AccountingSubjectImportErrorSchema] = Field(
        default_factory=list, description="失败明细"
    )
    errors_truncated: bool = Field(default=False, description="失败明细是否已截断")


class AccountingSubjectPageSchema(PageResultSchema):
    """会计科目主数据分页响应模型。"""

    items: list[AccountingSubjectOutSchema] = Field(
        default_factory=list, description="会计科目列表"
    )


class AccountingSubjectQueryParam:
    """会计科目主数据查询参数。"""

    def __init__(
        self,
        code: str | None = Query(None, description="会计科目代码"),
        name: str | None = Query(None, description="会计科目名称"),
        balance_direction: str | None = Query(None, description="科目余额方向"),
        accounting_statement_subject: str | None = Query(
            None, description="所属会计报表科目"
        ),
        management_category_paths: list[str] | None = Query(
            None, description="管理分类层级路径(JSON数组，可多选)"
        ),
        status: str | None = Query(None, description="状态"),
    ) -> None:
        for field, value in {
            "code": code,
            "name": name,
            "accounting_statement_subject": accounting_statement_subject,
        }.items():
            if value and value.strip():
                setattr(self, field, (QueueEnum.like.value, value.strip()))
        if status:
            self.status = (QueueEnum.eq.value, status)
        if balance_direction:
            self.balance_direction = (QueueEnum.eq.value, balance_direction.strip())
        if management_category_paths is not None:
            fields = (
                "management_category_level1",
                "management_category_level2",
                "management_category_level3",
            )
            path_conditions: list[dict[str, tuple[str, str]]] = []
            for raw_path in management_category_paths:
                try:
                    path = json.loads(raw_path)
                except (TypeError, json.JSONDecodeError):
                    continue
                if not isinstance(path, list) or not 1 <= len(path) <= len(fields):
                    continue
                values = [str(value).strip() for value in path]
                if not all(values):
                    continue
                path_conditions.append(
                    {
                        field: (QueueEnum.eq.value, value)
                        for field, value in zip(fields, values, strict=False)
                    }
                )
            self.management_category_paths = ("or", path_conditions)
