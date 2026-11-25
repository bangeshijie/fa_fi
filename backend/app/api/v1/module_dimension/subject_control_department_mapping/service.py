from typing import Any

from app.api.v1.module_dimension.accounting_subject.crud import AccountingSubjectCRUD
from app.api.v1.module_dimension.accounting_subject.schema import AccountingSubjectOptionSchema
from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.dept.crud import DeptCRUD
from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException

from .crud import SubjectControlDepartmentMappingCRUD
from .schema import (
    SubjectControlDepartmentMappingCreateSchema,
    SubjectControlDepartmentMappingOptionSchema,
    SubjectControlDepartmentMappingOptionsSchema,
    SubjectControlDepartmentMappingOutSchema,
    SubjectControlDepartmentMappingQueryParam,
    SubjectControlDepartmentMappingUpdateSchema,
)


class SubjectControlDepartmentMappingService:
    """科目主控部门映射主数据服务。"""

    OUTPUT_PRELOAD = [
        "created_by",
        "updated_by",
        "deleted_by",
        "accounting_subject",
        "department",
    ]

    @classmethod
    async def get_options_service(
        cls, auth: AuthSchema
    ) -> dict[str, list[dict[str, Any]]]:
        subjects = await AccountingSubjectCRUD(auth).get_list_crud(
            search={"status": ("eq", "0")}, order_by=[{"code": "asc"}], preload=[]
        )
        departments = await cls._get_second_level_departments(auth)
        return SubjectControlDepartmentMappingOptionsSchema(
            accounting_subjects=[
                AccountingSubjectOptionSchema.model_validate(item).model_dump()
                for item in subjects
            ],
            departments=[
                SubjectControlDepartmentMappingOptionSchema.model_validate(item).model_dump()
                for item in departments
            ],
        ).model_dump()

    @classmethod
    async def _get_second_level_departments(cls, auth: AuthSchema) -> list[Any]:
        """获取集团树第二级组织，即事业部。"""
        departments = await DeptCRUD(auth).get_list_crud(
            search={"status": ("eq", "0")}, order_by=[{"code": "asc"}], preload=[]
        )
        department_lookup = {int(item.id): item for item in departments}
        return [
            item
            for item in departments
            if item.parent_id is not None
            and department_lookup.get(int(item.parent_id)) is not None
            and department_lookup[int(item.parent_id)].parent_id is None
        ]

    @classmethod
    async def get_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        item = await SubjectControlDepartmentMappingCRUD(auth).get_by_id_crud(
            id=id, preload=cls.OUTPUT_PRELOAD
        )
        if not item:
            raise CustomException(msg="科目主控部门映射不存在")
        return SubjectControlDepartmentMappingOutSchema.model_validate(item).model_dump()

    @classmethod
    async def get_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: SubjectControlDepartmentMappingQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        return await SubjectControlDepartmentMappingCRUD(auth).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"updated_time": "desc"}],
            search=search.__dict__ if search else {},
            out_schema=SubjectControlDepartmentMappingOutSchema,
            preload=cls.OUTPUT_PRELOAD,
        )

    @classmethod
    async def _validate_relations(
        cls, auth: AuthSchema, accounting_subject_id: int, dept_id: int
    ) -> None:
        if not await AccountingSubjectCRUD(auth).get_by_id_crud(
            id=accounting_subject_id, preload=[]
        ):
            raise CustomException(msg="会计科目不存在")
        if not await DeptCRUD(auth).get(id=dept_id, preload=[]):
            raise CustomException(msg="部门不存在或当前用户无权访问")
        second_level_ids = {
            int(item.id) for item in await cls._get_second_level_departments(auth)
        }
        if dept_id not in second_level_ids:
            raise CustomException(msg="映射部门必须选择集团下第二级事业部")

    @classmethod
    async def create_service(
        cls, auth: AuthSchema, data: SubjectControlDepartmentMappingCreateSchema
    ) -> dict:
        crud = SubjectControlDepartmentMappingCRUD(auth)
        await cls._validate_relations(auth, data.accounting_subject_id, data.dept_id)
        if await crud.get(
            accounting_subject_id=data.accounting_subject_id, dept_id=data.dept_id
        ):
            raise CustomException(msg="创建失败，会计科目和部门组合已存在")
        item = await crud.create(data=data)
        return await cls.get_detail_service(auth=auth, id=item.id)

    @classmethod
    async def update_service(
        cls,
        auth: AuthSchema,
        id: int,
        data: SubjectControlDepartmentMappingUpdateSchema,
    ) -> dict:
        crud = SubjectControlDepartmentMappingCRUD(auth)
        if not await crud.get_by_id_crud(id=id, preload=[]):
            raise CustomException(msg="更新失败，科目主控部门映射不存在")
        await cls._validate_relations(auth, data.accounting_subject_id, data.dept_id)
        existing = await crud.get(
            accounting_subject_id=data.accounting_subject_id, dept_id=data.dept_id
        )
        if existing and existing.id != id:
            raise CustomException(msg="更新失败，会计科目和部门组合已存在")
        await crud.update(id=id, data=data)
        return await cls.get_detail_service(auth=auth, id=id)

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        crud = SubjectControlDepartmentMappingCRUD(auth)
        for id in ids:
            if not await crud.get_by_id_crud(id=id, preload=[]):
                raise CustomException(msg="删除失败，科目主控部门映射不存在")
        await crud.delete(ids=ids)

    @classmethod
    async def set_available_service(
        cls, auth: AuthSchema, data: BatchSetAvailable
    ) -> None:
        if not data.ids:
            raise CustomException(msg="状态修改失败，操作对象不能为空")
        if data.status not in {"0", "1"}:
            raise CustomException(msg="状态参数不正确")
        await SubjectControlDepartmentMappingCRUD(auth).set_available_crud(
            ids=data.ids, status=data.status
        )
