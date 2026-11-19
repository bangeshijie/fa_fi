from collections.abc import Sequence

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_crud import CRUDBase

from .model import CostCenterModel
from .schema import CostCenterCreateSchema, CostCenterUpdateSchema


class CostCenterCRUD(CRUDBase[CostCenterModel, CostCenterCreateSchema, CostCenterUpdateSchema]):
    """成本中心主数据数据层。"""

    def __init__(self, auth: AuthSchema) -> None:
        self.auth = auth
        super().__init__(model=CostCenterModel, auth=auth)

    async def get_by_id_crud(
        self, id: int, preload: list[str] | None = None
    ) -> CostCenterModel | None:
        return await self.get(id=id, preload=preload)

    async def get_list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
        preload: list[str] | None = None,
    ) -> Sequence[CostCenterModel]:
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def set_available_crud(self, ids: list[int], status: str) -> None:
        await self.set(ids=ids, status=status)
