"""预算明细 CRUD。"""

from collections.abc import Sequence

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_crud import CRUDBase

from .model import BudgetDetailModel
from .schema import BudgetDetailCreateSchema, BudgetDetailUpdateSchema


class BudgetDetailCRUD(CRUDBase[BudgetDetailModel, BudgetDetailCreateSchema, BudgetDetailUpdateSchema]):
    def __init__(self, auth: AuthSchema) -> None:
        self.auth = auth
        super().__init__(model=BudgetDetailModel, auth=auth)

    async def get_by_id_crud(
        self, id: int, preload: list[str] | None = None
    ) -> BudgetDetailModel | None:
        return await self.get(id=id, preload=preload)

    async def get_list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
        preload: list[str] | None = None,
    ) -> Sequence[BudgetDetailModel]:
        return await self.list(search=search, order_by=order_by, preload=preload)
