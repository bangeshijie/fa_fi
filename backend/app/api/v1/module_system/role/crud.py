from collections.abc import Sequence

from sqlalchemy import select

from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.dept.crud import DeptCRUD
from app.api.v1.module_system.menu.model import MenuModel
from app.core.base_crud import CRUDBase

from .model import RoleModel
from .schema import RoleCreateSchema, RoleUpdateSchema


class RoleCRUD(CRUDBase[RoleModel, RoleCreateSchema, RoleUpdateSchema]):
    """角色模块数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化角色数据层。

        参数:
        - auth (AuthSchema): 认证信息模型（含 DB 会话等上下文）。

        返回:
        - None
        """
        self.auth = auth
        super().__init__(model=RoleModel, auth=auth)

    async def get_by_id_crud(self, id: int, preload: list | None = None) -> RoleModel | None:
        """
        根据id获取角色信息

        参数:
        - id (int): 角色ID
        - preload (list | None): 预加载选项

        返回:
        - RoleModel | None: 角色模型对象
        """
        return await self.get(id=id, preload=preload)

    async def get_list_crud(
        self,
        search: dict | None = None,
        order_by: list | None = None,
        preload: list | None = None,
    ) -> Sequence[RoleModel]:
        """
        获取角色列表

        参数:
        - search (dict | None): 查询参数
        - order_by (list | None): 排序参数
        - preload (list | None): 预加载选项

        返回:
        - Sequence[RoleModel]: 角色模型对象列表
        """
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def set_role_menus_crud(self, role_ids: list[int], menu_ids: list[int]) -> None:
        """
        设置角色的菜单权限

        参数:
        - role_ids (list[int]): 角色ID列表
        - menu_ids (list[int]): 菜单ID列表

        返回:
        - None
        """
        roles = await self.list(search={"id": ("in", role_ids)})

        # 页面下的按钮权限可以部分勾选。此时页面节点会在前端树中处于
        # 半选状态，但仍必须保留页面及目录父级，否则用户登录后无法
        # 生成页面路由，页面查询接口也会缺少页面本身的权限标识。
        normalized_menu_ids = set(menu_ids)
        if normalized_menu_ids:
            result = await self.auth.db.execute(
                select(MenuModel.id, MenuModel.parent_id)
            )
            parent_map = {
                row.id: row.parent_id
                for row in result
            }

            for menu_id in tuple(normalized_menu_ids):
                current_id = menu_id
                visited: set[int] = set()
                while current_id in parent_map and current_id not in visited:
                    visited.add(current_id)
                    parent_id = parent_map[current_id]
                    if parent_id is None:
                        break
                    normalized_menu_ids.add(parent_id)
                    current_id = parent_id

        # 前端未勾选时 menu_ids 可能为空：此时应清空关联，而不是触发全量查询
        menus = (
            []
            if not normalized_menu_ids
            else (
                await self.auth.db.execute(
                    select(MenuModel).where(
                        MenuModel.id.in_(normalized_menu_ids)
                    )
                )
            ).scalars().all()
        )

        # 直接分配菜单，无需租户检查
        for obj in roles:
            relationship = obj.menus
            relationship.clear()
            relationship.extend(menus)
        await self.auth.db.flush()

    async def set_role_data_scope_crud(self, role_ids: list[int], data_scope: int) -> None:
        """
        设置角色的数据范围

        参数:
        - role_ids (list[int]): 角色ID列表
        - data_scope (int): 数据范围

        返回:
        - None
        """
        await self.set(ids=role_ids, data_scope=data_scope)

    async def set_role_depts_crud(self, role_ids: list[int], dept_ids: list[int]) -> None:
        """
        设置角色的部门权限

        参数:
        - role_ids (list[int]): 角色ID列表
        - dept_ids (list[int]): 部门ID列表

        返回:
        - None
        """
        roles = await self.list(search={"id": ("in", role_ids)})
        # 前端未勾选时 dept_ids 可能为空：此时应清空关联，而不是触发全量查询
        depts = (
            []
            if not dept_ids
            else await DeptCRUD(self.auth).get_list_crud(search={"id": ("in", dept_ids)})
        )

        for obj in roles:
            relationship = obj.depts
            relationship.clear()
            relationship.extend(depts)
        await self.auth.db.flush()

    async def set_available_crud(self, ids: list[int], status: str) -> None:
        """
        设置角色的可用状态

        参数:
        - ids (list[int]): 角色ID列表
        - status (str): 可用状态

        返回:
        - None
        """
        await self.set(ids=ids, status=status)
