import io
from typing import Any

import pandas as pd
from fastapi import UploadFile, status as http_status
from redis.asyncio.client import Redis
from sqlalchemy import select

from app.api.v1.module_system.dict.crud import DictDataCRUD, DictTypeCRUD
from app.api.v1.module_system.dict.schema import DictDataOutSchema
from app.api.v1.module_system.dict.service import DictDataService
from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.dept.crud import DeptCRUD
from app.api.v1.module_system.menu.crud import MenuCRUD
from app.api.v1.module_system.menu.model import MenuModel
from app.api.v1.module_system.menu.schema import MenuOutSchema
from app.api.v1.module_system.position.crud import PositionCRUD
from app.api.v1.module_system.role.crud import RoleCRUD
from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException
from app.core.logger import log
from app.utils.common_util import get_parent_id_map, traversal_to_tree
from app.utils.excel_util import ExcelUtil
from app.utils.hash_bcrpy_util import PwdUtil

from .crud import UserCRUD
from .schema import (
    CurrentUserUpdateSchema,
    ResetPasswordSchema,
    UserChangePasswordSchema,
    UserCreateSchema,
    UserForgetPasswordSchema,
    UserImportResultSchema,
    UserOutSchema,
    UserQueryParam,
    UserRegisterSchema,
    UserUpdateSchema,
)


class UserService:
    """用户模块服务层"""

    USER_SEX_DICT_TYPE = "sys_user_sex"

    @classmethod
    async def _get_enabled_sex_options(
        cls, auth: AuthSchema, redis: Redis | None = None
    ) -> list[DictDataOutSchema]:
        """读取启用的性别字典，优先使用 Redis，未命中时回源数据库。"""
        if redis is not None:
            cached_options = await DictDataService.get_init_dict_service(
                redis=redis,
                dict_type=cls.USER_SEX_DICT_TYPE,
            )
            options = [DictDataOutSchema.model_validate(item) for item in cached_options]
        else:
            # 保留无 Redis 调用方的数据库兜底，避免服务层被强制绑定到 Redis。
            dict_type = await DictTypeCRUD(auth).get(dict_type=cls.USER_SEX_DICT_TYPE)
            if not dict_type or dict_type.status != "0":
                raise CustomException(msg="用户性别字典不存在或已停用")
            options = list(
                await DictDataCRUD(auth).get_obj_list_by_dict_type_crud(
                    dict_type=cls.USER_SEX_DICT_TYPE,
                    status="0",
                )
            )

        if not options:
            raise CustomException(msg="未配置启用的用户性别字典")
        return sorted(options, key=lambda item: (item.dict_sort or 0, item.id or 0))

    @classmethod
    async def _resolve_sex_value(
        cls,
        auth: AuthSchema,
        value: str | None,
        use_default: bool = False,
        redis: Redis | None = None,
    ) -> str | None:
        """将字典标签或编码解析成当前启用字典中的编码。"""
        options = await cls._get_enabled_sex_options(auth=auth, redis=redis)
        if value is None or not str(value).strip():
            if not use_default:
                return value
            default = next((item for item in options if item.is_default), options[0])
            return str(default.dict_value)

        normalized = str(value).strip()
        for item in options:
            if normalized in {str(item.dict_value), str(item.dict_label).strip()}:
                return str(item.dict_value)

        raise CustomException(msg=f"性别值不存在或已停用: {value}")

    @classmethod
    async def _get_sex_label_map(
        cls, auth: AuthSchema, redis: Redis | None = None
    ) -> tuple[dict[str, str], dict[str, str], list[str]]:
        """生成 Excel 导入、导出和模板所需的动态字典映射。"""
        options = await cls._get_enabled_sex_options(auth=auth, redis=redis)
        label_to_value = {
            str(item.dict_label).strip(): str(item.dict_value)
            for item in options
            if item.dict_label is not None and item.dict_value is not None
        }
        value_to_label = {
            str(item.dict_value): str(item.dict_label)
            for item in options
            if item.dict_label is not None and item.dict_value is not None
        }
        labels = [
            str(item.dict_label)
            for item in options
            if item.dict_label is not None and item.dict_value is not None
        ]
        return label_to_value, value_to_label, labels

    @classmethod
    async def get_detail_by_id_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        根据ID获取用户详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 用户ID

        返回:
        - dict: 用户详情字典
        """
        user = await UserCRUD(auth).get_by_id_crud(id=id)
        if not user:
            raise CustomException(msg="用户不存在")

        return UserOutSchema.model_validate(user).model_dump()

    @classmethod
    async def get_user_list_service(
        cls,
        auth: AuthSchema,
        search: UserQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[dict]:
        """
        获取用户列表

        参数:
        - auth (AuthSchema): 认证信息模型
        - search (UserQueryParam | None): 查询参数对象。
        - order_by (list[dict[str, str]] | None): 排序参数列表。

        返回:
        - list[dict]: 用户详情字典列表
        """
        user_list = await UserCRUD(auth).get_list_crud(search=search.to_dict(), order_by=order_by)
        user_dict_list = []
        for user in user_list:
            user_dict = UserOutSchema.model_validate(user).model_dump()
            user_dict_list.append(user_dict)

        return user_dict_list

    @classmethod
    async def get_user_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: UserQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        """
        分页查询用户（数据库 OFFSET/LIMIT）。

        参数:
        - auth (AuthSchema): 认证信息模型
        - page_no (int): 页码（从 1 开始）
        - page_size (int): 每页条数
        - search (UserQueryParam | None): 查询条件
        - order_by (list[dict[str, str]] | None): 排序字段列表

        返回:
        - dict: 分页结果（结构由 `CRUD.page` 返回约定）
        """
        offset = (page_no - 1) * page_size
        return await UserCRUD(auth).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search.__dict__ if search else {},
            out_schema=UserOutSchema,
        )

    @classmethod
    async def create_user_service(
        cls, data: UserCreateSchema, auth: AuthSchema, redis: Redis | None = None
    ) -> dict:
        """
        创建用户

        参数:
        - data (UserCreateSchema): 用户创建信息
        - auth (AuthSchema): 认证信息模型

        返回:
        - dict: 创建后的用户详情字典
        """
        if not data.username:
            raise CustomException(msg="用户名不能为空")
        # 检查是否试图创建超级管理员
        if data.is_superuser:
            raise CustomException(msg="不允许创建超级管理员")
        # 检查用户名是否存在
        user = await UserCRUD(auth).get_by_username_crud(username=data.username)
        if user:
            raise CustomException(msg="已存在相同用户名称的账号")

        # 检查部门是否存在
        if data.dept_id:
            dept = await DeptCRUD(auth).get_by_id_crud(id=data.dept_id)
            if not dept:
                raise CustomException(msg="部门不存在")
        gender = await cls._resolve_sex_value(
            auth=auth, value=data.gender, use_default=True, redis=redis
        )
        # 创建用户
        if data.password:
            data.password = PwdUtil.set_password_hash(password=data.password)
        user_dict = data.model_dump(exclude_unset=True, exclude={"role_ids", "position_ids"})
        user_dict["gender"] = gender
        # 创建用户
        new_user = await UserCRUD(auth).create(data=user_dict)
        # 设置角色
        if data.role_ids and len(data.role_ids) > 0:
            await UserCRUD(auth).set_user_roles_crud(user_ids=[new_user.id], role_ids=data.role_ids)
        # 设置岗位
        if data.position_ids and len(data.position_ids) > 0:
            await UserCRUD(auth).set_user_positions_crud(
                user_ids=[new_user.id], position_ids=data.position_ids
            )

        new_user_dict = UserOutSchema.model_validate(new_user).model_dump()
        return new_user_dict

    @classmethod
    async def update_user_service(
        cls, id: int, data: UserUpdateSchema, auth: AuthSchema, redis: Redis | None = None
    ) -> dict:
        """
        更新用户

        参数:
        - id (int): 用户ID
        - data (UserUpdateSchema): 用户更新信息
        - auth (AuthSchema): 认证信息模型

        返回:
        - Dict: 更新后的用户详情字典
        """
        if not data.username:
            raise CustomException(msg="账号不能为空")

        # 检查用户是否存在
        user = await UserCRUD(auth).get_by_id_crud(id=id)
        if not user:
            raise CustomException(msg="用户不存在")

        # 检查是否尝试修改超级管理员
        if user.is_superuser:
            raise CustomException(msg="超级管理员不允许修改")

        # 检查用户名是否重复
        exist_user = await UserCRUD(auth).get_by_username_crud(username=data.username)
        if exist_user and exist_user.id != id:
            raise CustomException(msg="已存在相同的账号")
        # 新增：检查手机号是否重复
        if data.mobile:
            exist_mobile_user = await UserCRUD(auth).get_by_mobile_crud(mobile=data.mobile)
            if exist_mobile_user and exist_mobile_user.id != id:
                raise CustomException(msg="更新失败，手机号已存在")
        # 新增：检查邮箱是否重复
        if data.email:
            exist_email_user = await UserCRUD(auth).get(email=data.email)
            if exist_email_user and exist_email_user.id != id:
                raise CustomException(msg="更新失败，邮箱已存在")
        # 检查部门是否存在且可用
        if data.dept_id:
            dept = await DeptCRUD(auth).get_by_id_crud(id=data.dept_id)
            if not dept:
                raise CustomException(msg="部门不存在")
            if dept.status == "1":
                raise CustomException(msg="部门已被禁用")

        gender = None
        if data.gender is not None:
            gender = await cls._resolve_sex_value(auth=auth, value=data.gender, redis=redis)

        # 更新用户 - 排除不应被修改的字段, 更新不更新密码
        user_dict = data.model_dump(
            exclude_unset=True,
            exclude={"role_ids", "position_ids", "last_login", "password"},
        )
        if gender is not None:
            user_dict["gender"] = gender
        new_user = await UserCRUD(auth).update(id=id, data=user_dict)

        # 更新角色和岗位
        if data.role_ids and len(data.role_ids) > 0:
            # 检查角色是否都存在且可用
            roles = await RoleCRUD(auth).get_list_crud(search={"id": ("in", data.role_ids)})
            if len(roles) != len(data.role_ids):
                raise CustomException(msg="部分角色不存在")
            if not all(role.status for role in roles):
                raise CustomException(msg="部分角色已被禁用")
            await UserCRUD(auth).set_user_roles_crud(user_ids=[id], role_ids=data.role_ids)

        if data.position_ids and len(data.position_ids) > 0:
            # 检查岗位是否都存在且可用
            positions = await PositionCRUD(auth).get_list_crud(
                search={"id": ("in", data.position_ids)}
            )
            if len(positions) != len(data.position_ids):
                raise CustomException(msg="部分岗位不存在")
            if not all(position.status for position in positions):
                raise CustomException(msg="部分岗位已被禁用")
            await UserCRUD(auth).set_user_positions_crud(
                user_ids=[id], position_ids=data.position_ids
            )

        user_dict = UserOutSchema.model_validate(new_user).model_dump()
        return user_dict

    @classmethod
    async def delete_user_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除用户

        参数:
        - auth (AuthSchema): 认证信息模型
        - ids (list[int]): 用户ID列表

        返回:
        - None
        """
        if len(ids) < 1:
            raise CustomException(msg="删除失败，删除对象不能为空")
        for id in ids:
            user = await UserCRUD(auth).get_by_id_crud(id=id)
            if not user:
                raise CustomException(msg="用户不存在")
            if user.is_superuser:
                raise CustomException(msg="超级管理员不能删除")
            if user.status == "0":
                raise CustomException(msg="用户已启用,不能删除")
            if auth.user and auth.user.id == id:
                raise CustomException(msg="不能删除当前登陆用户")
        # 删除用户角色关联数据
        await UserCRUD(auth).set_user_roles_crud(user_ids=ids, role_ids=[])

        # 删除用户岗位关联数据
        await UserCRUD(auth).set_user_positions_crud(user_ids=ids, position_ids=[])

        # 删除用户
        await UserCRUD(auth).delete(ids=ids)

    @classmethod
    async def get_current_user_info_service(cls, auth: AuthSchema) -> dict:
        """
        获取当前用户信息

        参数:
        - auth (AuthSchema): 认证信息模型

        返回:
        - Dict: 当前用户详情字典
        """
        # 获取用户基本信息
        if not auth.user or not auth.user.id:
            raise CustomException(msg="用户不存在")
        user = await UserCRUD(auth).get_by_id_crud(id=auth.user.id)
        user_dict = UserOutSchema.model_validate(user).model_dump()

        # 获取菜单权限（PC 管理端侧栏：仅 client=pc）
        _pc_only = {"client": "pc"}
        if auth.user and auth.user.is_superuser:
            # 使用树形结构查询，预加载children关系
            menu_all = await MenuCRUD(auth).get_tree_list_crud(
                search={"type": ("in", [1, 2, 4]), "status": "0", **_pc_only},
                order_by=[{"order": "asc"}],
            )
            menus = [MenuOutSchema.model_validate(menu).model_dump() for menu in menu_all]

        else:
            # 收集用户所有角色已授权的菜单/按钮 ID（仅 PC 端）。
            #
            # 按钮权限（type=3）可能被部分勾选。此时页面节点（type=2）
            # 在前端树中是半选状态，不会出现在 getCheckedKeys(false) 的结果里，
            # 但页面仍然必须可见。因此下面会为每个已授权节点补齐所有父级。
            assigned_menu_ids = {
                menu.id
                for role in auth.user.roles or []
                for menu in role.menus
                if menu.status == "0"
                and getattr(menu, "client", "pc") == "pc"
            }

            if not assigned_menu_ids:
                menus = []
            else:
                # 这里需要读取完整的启用菜单树来补齐父级。
                # 不能通过 MenuCRUD 查询，因为 MenuCRUD 会再次套用当前用户
                # 的角色菜单过滤，未直接授权但必须展示的父级会被过滤掉。
                result = await auth.db.execute(
                    select(MenuModel)
                    .where(
                        MenuModel.status == "0",
                        MenuModel.client == "pc",
                    )
                    .order_by(MenuModel.order.asc())
                )
                all_menus = list(result.scalars().all())
                parent_map = get_parent_id_map(all_menus)
                visible_ids: set[int] = set()

                for menu_id in assigned_menu_ids:
                    if menu_id not in parent_map:
                        continue

                    # 包含按钮自身、页面节点及所有目录父级。
                    chain: list[int] = []
                    current_id: int | None = menu_id
                    while current_id is not None and current_id in parent_map:
                        chain.append(current_id)
                        current_id = parent_map[current_id]

                    # 只有能回溯到根节点的菜单链才加入导航，避免异常数据
                    # 形成脱离目录的孤立页面。
                    if current_id is None:
                        visible_ids.update(chain)

                menus = [
                    MenuOutSchema.model_validate(menu).model_dump()
                    for menu in all_menus
                    if menu.id in visible_ids
                ]
        user_dict["menus"] = traversal_to_tree(menus)
        return user_dict

    @classmethod
    async def update_current_user_info_service(
        cls, auth: AuthSchema, data: CurrentUserUpdateSchema, redis: Redis | None = None
    ) -> dict:
        """
        更新当前用户信息

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (CurrentUserUpdateSchema): 当前用户更新信息

        返回:
        - Dict: 更新后的当前用户详情字典
        """
        if not auth.user or not auth.user.id:
            raise CustomException(msg="用户不存在")
        user = await UserCRUD(auth).get_by_id_crud(id=auth.user.id)
        if not user:
            raise CustomException(msg="用户不存在")
        # 新增：检查手机号是否重复
        if data.mobile:
            exist_mobile_user = await UserCRUD(auth).get_by_mobile_crud(mobile=data.mobile)
            if exist_mobile_user and exist_mobile_user.id != auth.user.id:
                raise CustomException(msg="更新失败，手机号已存在")
        # 新增：检查邮箱是否重复
        if data.email:
            exist_email_user = await UserCRUD(auth).get(email=data.email)
            if exist_email_user and exist_email_user.id != auth.user.id:
                raise CustomException(msg="更新失败，邮箱已存在")
        update_data = data.model_dump(exclude_unset=True)
        if data.gender is not None:
            update_data["gender"] = await cls._resolve_sex_value(
                auth=auth, value=data.gender, redis=redis
            )
        user_update_data = UserUpdateSchema(**update_data)
        new_user = await UserCRUD(auth).update(id=auth.user.id, data=user_update_data)
        return UserOutSchema.model_validate(new_user).model_dump()

    @classmethod
    async def set_user_available_service(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        """
        设置用户状态

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (BatchSetAvailable): 批量设置用户状态数据

        返回:
        - None
        """
        for id in data.ids:
            user = await UserCRUD(auth).get_by_id_crud(id=id)
            if not user:
                raise CustomException(msg=f"用户ID {id} 不存在")
            if user.is_superuser:
                raise CustomException(msg="超级管理员状态不能修改")
        await UserCRUD(auth).set_available_crud(ids=data.ids, status=data.status)

    @classmethod
    async def change_user_password_service(
        cls, auth: AuthSchema, data: UserChangePasswordSchema
    ) -> dict:
        """
        修改用户密码

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (UserChangePasswordSchema): 用户密码修改数据

        返回:
        - Dict: 更新后的当前用户详情字典
        """
        if not auth.user or not auth.user.id:
            raise CustomException(msg="用户不存在")
        if not data.old_password or not data.new_password:
            raise CustomException(msg="密码不能为空")

        # 验证原密码
        user = await UserCRUD(auth).get_by_id_crud(id=auth.user.id)
        if not user:
            raise CustomException(msg="用户不存在")
        if not PwdUtil.verify_password(
            plain_password=data.old_password, password_hash=user.password
        ):
            raise CustomException(msg="原密码输入错误")

        # 更新密码
        new_password_hash = PwdUtil.set_password_hash(password=data.new_password)
        new_user = await UserCRUD(auth).change_password_crud(
            id=user.id, password_hash=new_password_hash
        )
        return UserOutSchema.model_validate(new_user).model_dump()

    @classmethod
    async def reset_user_password_service(cls, auth: AuthSchema, data: ResetPasswordSchema) -> dict:
        """
        重置用户密码

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (ResetPasswordSchema): 用户密码重置数据

        返回:
        - Dict: 更新后的当前用户详情字典
        """
        if not data.password:
            raise CustomException(msg="密码不能为空")

        # 验证用户
        user = await UserCRUD(auth).get_by_id_crud(id=data.id)
        if not user:
            raise CustomException(msg="用户不存在")

        # 检查是否是超级管理员
        if user.is_superuser:
            raise CustomException(msg="超级管理员密码不能重置")

        # 更新密码
        new_password_hash = PwdUtil.set_password_hash(password=data.password)
        new_user = await UserCRUD(auth).change_password_crud(
            id=data.id, password_hash=new_password_hash
        )
        return UserOutSchema.model_validate(new_user).model_dump()

    @classmethod
    async def register_user_service(cls, auth: AuthSchema, data: UserRegisterSchema) -> dict:
        """
        用户注册

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (UserRegisterSchema): 用户注册数据

        返回:
        - Dict: 注册后的用户详情字典
        """
        # 检查用户名是否存在
        username_ok = await UserCRUD(auth).get_by_username_crud(username=data.username)
        if username_ok:
            raise CustomException(msg="账号已存在")

        data.password = PwdUtil.set_password_hash(password=data.password)
        data.name = data.username
        create_dict = data.model_dump(exclude_unset=True, exclude={"role_ids", "position_ids"})

        # 设置创建人ID
        if auth.user and auth.user.id:
            create_dict["created_id"] = auth.user.id

        result = await UserCRUD(auth).create(data=create_dict)
        if data.role_ids:
            await UserCRUD(auth).set_user_roles_crud(user_ids=[result.id], role_ids=data.role_ids)
        return UserOutSchema.model_validate(result).model_dump()

    @classmethod
    async def forget_password_service(
        cls, auth: AuthSchema, data: UserForgetPasswordSchema
    ) -> dict:
        """
        用户忘记密码

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (UserForgetPasswordSchema): 用户忘记密码数据

        返回:
        - Dict: 更新后的当前用户详情字典
        """
        user = await UserCRUD(auth).get_by_username_crud(username=data.username)
        if not user:
            raise CustomException(msg="用户不存在")
        if user.status == "1":
            raise CustomException(msg="用户已停用")

        # 检查是否是超级管理员
        if user.is_superuser:
            raise CustomException(msg="超级管理员密码不能重置")

        new_password_hash = PwdUtil.set_password_hash(password=data.new_password)
        new_user = await UserCRUD(auth).forget_password_crud(
            id=user.id, password_hash=new_password_hash
        )
        return UserOutSchema.model_validate(new_user).model_dump()

    @classmethod
    async def batch_import_user_service(
        cls,
        auth: AuthSchema,
        file: UploadFile,
        update_support: bool = False,
        redis: Redis | None = None,
    ) -> dict[str, Any]:
        """
        批量导入用户，并返回可供前端展示的批次结果。

        参数:
        - auth (AuthSchema): 认证信息模型
        - file (UploadFile): 上传的Excel文件
        - update_support (bool, optional): 是否支持更新已存在用户. 默认值为False.

        导入策略:
        - 文件格式、表头错误直接返回 4xx，不进入数据库写入。
        - 单行错误只回滚当前行，其他合法行继续导入。
        - 已存在账号计为重复项；当前接口开启更新时，同时计为更新成功。
        - 没有任何一行成功时返回 422，避免把完全失败误报为成功。
        """

        header_dict = {
            "部门编号": "dept_id",
            "账号": "username",
            "昵称": "name",
            "邮箱": "email",
            "手机号": "mobile",
            "性别": "gender",
            "状态": "status",
        }

        try:
            filename = (file.filename or "").lower()
            if not filename.endswith((".xlsx", ".xls")):
                raise CustomException(
                    msg="仅支持 .xlsx 或 .xls 格式的 Excel 文件",
                    status_code=http_status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            try:
                contents = await file.read()
                df = pd.read_excel(io.BytesIO(contents))
            except Exception as e:
                log.error(f"读取用户导入 Excel 失败: {e!s}")
                raise CustomException(
                    msg="Excel 文件无法读取，请确认文件未损坏且格式正确",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                ) from e
            finally:
                await file.close()

            if df.empty:
                raise CustomException(
                    msg="导入文件为空",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            # 允许用户在表头前后误加空格，但不改变模板字段含义。
            df.columns = [str(column).strip() for column in df.columns]

            # 检查表头是否完整
            missing_headers = [header for header in header_dict if header not in df.columns]
            if missing_headers:
                raise CustomException(
                    msg=f"导入文件缺少必要的列: {', '.join(missing_headers)}",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            # 重命名列名
            df.rename(columns=header_dict, inplace=True)

            # 验证必填字段
            required_fields = ["username", "name", "dept_id"]
            required_errors = []
            for field in required_fields:
                missing_rows = df[df[field].isnull()].index.tolist()
                if missing_rows:
                    field_name = next(key for key, value in header_dict.items() if value == field)
                    rows_str = "、".join([str(index + 1) for index in missing_rows])
                    required_errors.append(f"{field_name}不能为空，第{rows_str}行")

            if required_errors:
                raise CustomException(
                    msg="；".join(required_errors),
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            sex_options = await cls._get_enabled_sex_options(auth=auth, redis=redis)
            if not sex_options:
                raise CustomException(msg="用户性别字典没有可用选项")

            sex_label_to_value = {
                str(item.dict_label).strip(): str(item.dict_value)
                for item in sex_options
                if item.dict_label is not None and item.dict_value is not None
            }
            default_sex = next((item for item in sex_options if item.is_default), sex_options[0])
            default_sex_value = str(default_sex.dict_value)
            allowed_sex_values = {str(item.dict_value) for item in sex_options}

            total_count = len(df.index)
            created_count = 0
            updated_count = 0
            duplicate_count = 0
            failed_count = 0
            errors: list[dict[str, Any]] = []
            errors_truncated = False

            # 处理每一行数据
            for row_number, (_index, row) in enumerate(df.iterrows(), start=2):
                username: str | None = None
                try:
                    username = cls._excel_text(row.get("username"))
                    name = cls._excel_text(row.get("name"))
                    if not username:
                        raise CustomException(msg="账号不能为空")
                    if not name:
                        raise CustomException(msg="昵称不能为空")

                    # 数据转换
                    raw_gender = cls._excel_text(row.get("gender")) or ""
                    gender = sex_label_to_value.get(raw_gender, raw_gender or default_sex_value)
                    if gender not in allowed_sex_values:
                        raise CustomException(msg=f"性别选项不存在或已停用: {raw_gender}")

                    raw_status = cls._excel_text(row.get("status"))
                    status_map = {
                        "正常": "0",
                        "启用": "0",
                        "0": "0",
                        "停用": "1",
                        "禁用": "1",
                        "1": "1",
                    }
                    status = status_map.get(raw_status or "正常")
                    if status is None:
                        raise CustomException(msg=f"状态只能填写正常/停用，当前值: {raw_status}")

                    dept_id = cls._excel_int(row.get("dept_id"), "部门编号")

                    # 构建用户数据
                    user_data = {
                        "username": username,
                        "name": name,
                        "email": cls._excel_text(row.get("email")),
                        "mobile": cls._excel_text(row.get("mobile")),
                        "gender": gender,
                        "status": status,
                        "dept_id": dept_id,
                    }

                    # 每一行使用 SAVEPOINT，避免单行数据库错误影响后续行。
                    async with auth.db.begin_nested():
                        exists_user = await UserCRUD(auth).get_by_username_crud(
                            username=user_data["username"]
                        )
                        if exists_user:
                            duplicate_count += 1
                            if exists_user.is_superuser:
                                raise CustomException(msg="超级管理员不允许修改")
                            if not update_support:
                                raise CustomException(msg=f"用户 {username} 已存在")

                            # 导入更新不重置已有用户密码。
                            update_data = UserUpdateSchema(**user_data)
                            await cls.update_user_service(
                                id=exists_user.id,
                                data=update_data,
                                auth=auth,
                                redis=redis,
                            )
                            updated_count += 1
                        else:
                            # 新用户使用统一创建逻辑，服务层负责密码哈希和关联校验。
                            user_create_data = UserCreateSchema(
                                **user_data,
                                password="123456",
                            )
                            await cls.create_user_service(
                                data=user_create_data,
                                auth=auth,
                                redis=redis,
                            )
                            created_count += 1

                except Exception as e:
                    failed_count += 1
                    if len(errors) < cls.IMPORT_ERROR_PREVIEW_LIMIT:
                        errors.append(
                            {
                                "row_number": row_number,
                                "username": username,
                                "reason": str(e),
                            }
                        )
                    else:
                        errors_truncated = True
                    continue

            result = UserImportResultSchema(
                total_count=total_count,
                success_count=created_count + updated_count,
                created_count=created_count,
                updated_count=updated_count,
                duplicate_count=duplicate_count,
                failed_count=failed_count,
                errors=errors,
                errors_truncated=errors_truncated,
            )

            if result.success_count == 0:
                raise CustomException(
                    msg="导入未成功：没有任何数据通过校验并写入系统",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    data=result.model_dump(),
                )

            return result.model_dump()

        except CustomException:
            raise
        except Exception as e:
            log.error(f"批量导入用户失败: {e!s}")
            raise CustomException(
                msg="导入失败，请检查文件格式和数据内容",
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            ) from e

    IMPORT_ERROR_PREVIEW_LIMIT = 200

    @staticmethod
    def _excel_text(value: Any) -> str | None:
        """将 Excel 单元格安全转换为非空文本。"""
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        text = str(value).strip()
        return text or None

    @classmethod
    def _excel_int(cls, value: Any, field_name: str) -> int:
        """将 Excel 单元格转换为整数并给出友好错误。"""
        text = cls._excel_text(value)
        if text is None:
            raise CustomException(msg=f"{field_name}不能为空")
        try:
            number = float(text)
        except (TypeError, ValueError) as e:
            raise CustomException(msg=f"{field_name}必须为整数，当前值: {text}") from e
        if not number.is_integer():
            raise CustomException(msg=f"{field_name}必须为整数，当前值: {text}")
        return int(number)

    @classmethod
    async def get_import_template_user_service(
        cls, auth: AuthSchema, redis: Redis | None = None
    ) -> bytes:
        """
        获取用户导入模板

        返回:
        - bytes: Excel文件字节流
        """
        header_list = [
            "部门编号",
            "账号",
            "昵称",
            "邮箱",
            "手机号",
            "性别",
            "状态",
        ]
        selector_header_list = ["性别", "状态"]
        _, _, sex_labels = await cls._get_sex_label_map(auth=auth, redis=redis)
        option_list = [
            {"性别": sex_labels},
            {"状态": ["正常", "停用"]},
        ]
        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list,
        )

    @classmethod
    async def export_user_list_service(
        cls, user_list: list[dict[str, Any]], auth: AuthSchema, redis: Redis | None = None
    ) -> bytes:
        """
        导出用户列表为Excel文件

        参数:
        - user_list (list[dict[str, Any]]): 用户列表

        返回:
        - bytes: Excel文件字节流
        """
        if not user_list:
            raise CustomException(msg="没有数据可导出")

        _, sex_value_to_label, _ = await cls._get_sex_label_map(auth=auth, redis=redis)

        # 定义字段映射
        mapping_dict = {
            "id": "用户编号",
            "avatar": "头像",
            "username": "用户名称",
            "name": "用户昵称",
            "dept_name": "部门",
            "email": "邮箱",
            "mobile": "手机号",
            "gender": "性别",
            "status": "状态",
            "is_superuser": "是否超级管理员",
            "last_login": "最后登录时间",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
            "updated_id": "更新者ID",
        }

        # 复制数据并转换
        # creator = {'id': 1, 'name': '管理员', 'username': 'admin'}
        data = user_list.copy()
        for item in data:
            item["status"] = "启用" if item.get("status") == "0" else "停用"
            gender = item.get("gender")
            item["gender"] = sex_value_to_label.get(str(gender), str(gender) if gender is not None else "")
            item["is_superuser"] = "是" if item.get("is_superuser") else "否"
            item["creator"] = (
                item.get("creator", {}).get("name", "未知")
                if isinstance(item.get("creator"), dict)
                else "未知"
            )

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)
