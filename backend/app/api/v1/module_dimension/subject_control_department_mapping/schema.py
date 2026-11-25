from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import QueueEnum
from app.common.request import PageResultSchema
from app.core.base_schema import BaseSchema, UserBySchema


class SubjectControlDepartmentMappingCreateSchema(BaseModel):
    """科目主控部门映射创建模型。"""

    accounting_subject_id: int = Field(..., ge=1, description="会计科目ID")
    dept_id: int = Field(..., ge=1, description="所属事业部ID")
    control_department: str = Field(..., min_length=1, max_length=128, description="主控部门")
    control_person: str = Field(..., min_length=1, max_length=64, description="主控人")
    status: str = Field(default="0", description="状态(0:正常 1:停用)")
    description: str | None = Field(default=None, max_length=500, description="备注")

    @field_validator("control_department", "control_person", mode="before")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise ValueError("主控部门和主控人不能为空")
        return value

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class SubjectControlDepartmentMappingUpdateSchema(
    SubjectControlDepartmentMappingCreateSchema
):
    """科目主控部门映射更新模型。"""


class SubjectControlDepartmentMappingOutSchema(
    SubjectControlDepartmentMappingCreateSchema, BaseSchema, UserBySchema
):
    """科目主控部门映射响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    accounting_subject_code: str | None = Field(default=None, description="会计科目代码")
    accounting_subject_name: str | None = Field(default=None, description="会计科目名称")
    dept_code: str | None = Field(default=None, description="事业部编码")
    dept_name: str | None = Field(default=None, description="事业部名称")


class SubjectControlDepartmentMappingPageSchema(PageResultSchema):
    items: list[SubjectControlDepartmentMappingOutSchema] = Field(default_factory=list)


class SubjectControlDepartmentMappingOptionSchema(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class SubjectControlDepartmentMappingOptionsSchema(BaseModel):
    accounting_subjects: list[SubjectControlDepartmentMappingOptionSchema] = Field(
        default_factory=list
    )
    departments: list[SubjectControlDepartmentMappingOptionSchema] = Field(
        default_factory=list
    )


class SubjectControlDepartmentMappingQueryParam:
    """科目主控部门映射查询参数。"""

    def __init__(
        self,
        accounting_subject_id: int | None = Query(None, ge=1, description="会计科目ID"),
        dept_id: int | None = Query(None, ge=1, description="所属事业部ID"),
        control_department: str | None = Query(None, description="主控部门"),
        control_person: str | None = Query(None, description="主控人"),
        status: str | None = Query(None, description="状态"),
    ) -> None:
        if accounting_subject_id is not None:
            self.accounting_subject_id = (QueueEnum.eq.value, accounting_subject_id)
        if dept_id is not None:
            self.dept_id = (QueueEnum.eq.value, dept_id)
        for field, value in {
            "control_department": control_department,
            "control_person": control_person,
        }.items():
            if value and value.strip():
                setattr(self, field, (QueueEnum.like.value, value.strip()))
        if status:
            self.status = (QueueEnum.eq.value, status)
