from collections.abc import Sequence

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_crud import CRUDBase

from .model import SubjectControlDepartmentMappingModel
from .schema import (
    SubjectControlDepartmentMappingCreateSchema,
    SubjectControlDepartmentMappingUpdateSchema,
)


class SubjectControlDepartmentMappingCRUD(
    CRUDBase[
        SubjectControlDepartmentMappingModel,
        SubjectControlDepartmentMappingCreateSchema,
        SubjectControlDepartmentMappingUpdateSchema,
    ]
):
    """科目主控部门映射数据层。"""

    def __init__(self, auth: AuthSchema) -> None:
        self.auth = auth
        super().__init__(model=SubjectControlDepartmentMappingModel, auth=auth)

    async def get_by_id_crud(
        self, id: int, preload: list[str] | None = None
    ) -> SubjectControlDepartmentMappingModel | None:
        return await self.get(id=id, preload=preload)

    async def get_list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
        preload: list[str] | None = None,
    ) -> Sequence[SubjectControlDepartmentMappingModel]:
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def set_available_crud(self, ids: list[int], status: str) -> None:
        await self.set(ids=ids, status=status)
