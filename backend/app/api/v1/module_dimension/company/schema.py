import re
from decimal import Decimal

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import QueueEnum
from app.common.request import PageResultSchema
from app.core.base_schema import BaseSchema, UserBySchema
from app.core.validator import DateTimeStr


class CompanyCreateSchema(BaseModel):
    """公司主数据创建模型。"""

    code: str = Field(..., min_length=2, max_length=32, description="公司代码")
    name: str = Field(..., min_length=1, max_length=128, description="公司名称")
    holding_company_id: int | None = Field(default=None, ge=1, description="上级控股公司ID")
    address: str | None = Field(default=None, max_length=255, description="公司地址")
    phone: str | None = Field(default=None, max_length=32, description="公司电话")
    business_license_no: str | None = Field(
        default=None, max_length=64, description="营业执照号码"
    )
    leader: str | None = Field(default=None, max_length=64, description="公司负责人")
    holding_ratio: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2, description="控股比例(%)"
    )
    registered_capital: Decimal | None = Field(
        default=None, ge=0, max_digits=18, decimal_places=2, description="注册资本(万元)"
    )
    status: str = Field(default="0", description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=500, description="备注")

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = str(value or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,31}", value):
            raise ValueError("公司代码需为2-32位字母、数字、下划线或短横线")
        return value

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise ValueError("公司名称不能为空")
        return value

    @field_validator("address", "phone", "business_license_no", "leader", "description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class CompanyUpdateSchema(CompanyCreateSchema):
    """公司主数据更新模型。"""


class CompanyOutSchema(CompanyCreateSchema, BaseSchema, UserBySchema):
    """公司主数据响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    holding_company_code: str | None = Field(default=None, description="上级控股公司代码")
    holding_company_name: str | None = Field(default=None, description="上级控股公司名称")


class CompanyOptionSchema(BaseModel):
    """公司选择项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class CompanyPageSchema(PageResultSchema):
    """公司主数据分页响应模型。"""

    items: list[CompanyOutSchema] = Field(default_factory=list, description="公司列表")


class CompanyQueryParam:
    """公司主数据查询参数。"""

    def __init__(
        self,
        code: str | None = Query(None, description="公司代码"),
        name: str | None = Query(None, description="公司名称"),
        address: str | None = Query(None, description="公司地址"),
        phone: str | None = Query(None, description="公司电话"),
        business_license_no: str | None = Query(None, description="营业执照号码"),
        leader: str | None = Query(None, description="公司负责人"),
        status: str | None = Query(None, description="状态"),
        created_time: list[DateTimeStr] | None = Query(
            None,
            description="创建时间范围",
            examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"],
        ),
        updated_time: list[DateTimeStr] | None = Query(
            None,
            description="更新时间范围",
            examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"],
        ),
    ) -> None:
        for field, value in {
            "code": code,
            "name": name,
            "address": address,
            "phone": phone,
            "business_license_no": business_license_no,
            "leader": leader,
        }.items():
            if value and value.strip():
                setattr(self, field, (QueueEnum.like.value, value.strip()))

        if status:
            self.status = (QueueEnum.eq.value, status)
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = (QueueEnum.between.value, (updated_time[0], updated_time[1]))
