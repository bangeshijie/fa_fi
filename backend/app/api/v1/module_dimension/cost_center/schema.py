import re
from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import QueueEnum
from app.common.request import PageResultSchema
from app.core.base_schema import BaseSchema, UserBySchema
from app.core.validator import DateStr
from app.utils.time_util import now_beijing_naive


class CostCenterCreateSchema(BaseModel):
    """成本中心主数据创建模型。"""

    code: str = Field(..., min_length=2, max_length=32, description="成本中心代码")
    name: str = Field(..., min_length=1, max_length=128, description="成本中心名称")
    company_id: int = Field(..., ge=1, description="所属公司ID")
    function_scope: str = Field(..., min_length=4, max_length=4, description="职能范围")
    dept_id: int = Field(..., ge=1, description="所属组织部门ID")
    leader: str | None = Field(default=None, max_length=64, description="成本中心负责人")
    enable_time: DateStr = Field(
        default_factory=lambda: now_beijing_naive().date(), description="启用日期"
    )
    status: str = Field(default="0", description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=500, description="备注")

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = str(value or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,31}", value):
            raise ValueError("成本中心代码需为2-32位字母、数字、下划线或短横线")
        return value

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise ValueError("成本中心名称不能为空")
        return value

    @field_validator("function_scope", mode="before")
    @classmethod
    def validate_function_scope(cls, value: str) -> str:
        value = str(value or "").strip()
        if not re.fullmatch(r"\d{4}", value):
            raise ValueError("职能范围必须为4位数字，例如4000、5000或5500")
        return value

    @field_validator("leader", "description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class CostCenterUpdateSchema(CostCenterCreateSchema):
    """成本中心主数据更新模型。"""


class CostCenterOutSchema(CostCenterCreateSchema, BaseSchema, UserBySchema):
    """成本中心主数据响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    company_code: str | None = Field(default=None, description="所属公司代码")
    company_name: str | None = Field(default=None, description="所属公司名称")
    dept_code: str | None = Field(default=None, description="所属组织部门代码")
    dept_name: str | None = Field(default=None, description="所属组织部门名称")


class CostCenterOptionSchema(BaseModel):
    """成本中心关联选项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class DepartmentOptionSchema(BaseModel):
    """成本中心所属组织选项。"""

    id: int
    code: str
    name: str
    parent_id: int | None = None


class CostCenterImportErrorSchema(BaseModel):
    """成本中心导入单行错误。"""

    row_number: int = Field(..., description="Excel行号")
    code: str | None = Field(default=None, description="成本中心代码")
    reason: str = Field(..., description="失败原因")


class CostCenterImportResultSchema(BaseModel):
    """成本中心导入批次结果。"""

    total_count: int = Field(default=0, description="数据总行数")
    success_count: int = Field(default=0, description="成功处理行数")
    created_count: int = Field(default=0, description="新增成本中心数")
    updated_count: int = Field(default=0, description="更新成本中心数")
    duplicate_count: int = Field(default=0, description="已存在代码数")
    failed_count: int = Field(default=0, description="失败行数")
    errors: list[CostCenterImportErrorSchema] = Field(default_factory=list, description="失败明细")
    errors_truncated: bool = Field(default=False, description="失败明细是否已截断")


class CostCenterPageSchema(PageResultSchema):
    """成本中心主数据分页响应模型。"""

    items: list[CostCenterOutSchema] = Field(default_factory=list, description="成本中心列表")


class CostCenterQueryParam:
    """成本中心主数据查询参数。"""

    def __init__(
        self,
        code: str | None = Query(None, description="成本中心代码"),
        name: str | None = Query(None, description="成本中心名称"),
        company_id: int | None = Query(None, ge=1, description="所属公司ID"),
        function_scope: str | None = Query(None, description="职能范围"),
        dept_id: int | None = Query(None, ge=1, description="所属组织部门ID"),
        leader: str | None = Query(None, description="成本中心负责人"),
        status: str | None = Query(None, description="状态"),
    ) -> None:
        for field, value in {
            "code": code,
            "name": name,
            "function_scope": function_scope,
            "leader": leader,
        }.items():
            if value and value.strip():
                setattr(self, field, (QueueEnum.like.value, value.strip()))

        if company_id is not None:
            self.company_id = (QueueEnum.eq.value, company_id)
        if dept_id is not None:
            self.dept_id = (QueueEnum.eq.value, dept_id)
        if status:
            self.status = (QueueEnum.eq.value, status)
