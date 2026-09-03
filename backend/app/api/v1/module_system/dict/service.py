from redis.asyncio.client import Redis

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.enums import RedisInitKeyConfig
from app.config.setting import settings
from app.core.base_schema import BatchSetAvailable
from app.core.database import async_db_session
from app.core.exceptions import CustomException
from app.core.logger import log
from app.core.redis_crud import RedisCURD
from app.utils.excel_util import ExcelUtil

from .crud import DictDataCRUD, DictTypeCRUD
from .schema import (
    DictDataCreateSchema,
    DictDataOutSchema,
    DictDataQueryParam,
    DictDataUpdateSchema,
    DictTypeCreateSchema,
    DictTypeOutSchema,
    DictTypeQueryParam,
    DictTypeUpdateSchema,
)


def _dict_cache_key(dict_type: str) -> str:
    """生成字典数据缓存键。"""
    return f"{RedisInitKeyConfig.SYSTEM_DICT.key}:{dict_type}"


def _active_dict_cache_items(value: object) -> list[dict] | None:
    """校验并过滤字典缓存，只返回启用的字典项。"""
    if not isinstance(value, list):
        return None

    items = []
    for item in value:
        if not isinstance(item, dict) or item.get("status") != "0":
            continue
        items.append(item)

    return sorted(
        items,
        key=lambda item: (item.get("dict_sort") or 0, item.get("id") or 0),
    )


class DictTypeService:
    """
    字典类型管理模块服务层
    """

    @classmethod
    async def get_obj_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        获取数据字典类型详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 数据字典类型ID

        返回:
        - dict: 数据字典类型详情字典
        """
        obj = await DictTypeCRUD(auth).get_obj_by_id_crud(id=id)
        return DictTypeOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def get_obj_list_service(
        cls,
        auth: AuthSchema,
        search: DictTypeQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[dict]:
        """
        获取数据字典类型列表

        参数:
        - auth (AuthSchema): 认证信息模型
        - search (DictTypeQueryParam | None): 搜索条件模型
        - order_by (list[dict] | None): 排序字段列表

        返回:
        - list[dict]: 数据字典类型详情字典列表
        """
        obj_list = await DictTypeCRUD(auth).get_obj_list_crud(
            search=search.__dict__ if search else None,
            order_by=order_by,
        )
        return [DictTypeOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def get_obj_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: DictTypeQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> dict:
        """
        分页查询字典类型（数据库 OFFSET/LIMIT）。

        参数:
        - auth (AuthSchema): 认证信息模型
        - page_no (int): 页码（从 1 开始）
        - page_size (int): 每页条数
        - search (DictTypeQueryParam | None): 查询条件
        - order_by (list[dict] | None): 排序字段列表

        返回:
        - dict: 分页结果（结构由 `CRUD.page` 返回约定）
        """
        offset = (page_no - 1) * page_size
        return await DictTypeCRUD(auth).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search.__dict__ if search else {},
            out_schema=DictTypeOutSchema,
        )

    @classmethod
    async def create_obj_service(
        cls, auth: AuthSchema, redis: Redis, data: DictTypeCreateSchema
    ) -> dict:
        """
        创建数据字典类型

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis客户端
        - data (DictTypeCreateSchema): 数据字典类型创建模型

        返回:
        - dict: 数据字典类型详情字典
        """
        exist_obj = await DictTypeCRUD(auth).get(dict_name=data.dict_name)
        if exist_obj:
            raise CustomException(msg="创建失败，该数据字典类型已存在")
        obj = await DictTypeCRUD(auth).create_obj_crud(data=data)

        new_obj_dict = DictTypeOutSchema.model_validate(obj).model_dump()

        # 新类型暂时没有字典项，不写入空字符串占位缓存。
        # 首次读取时由 get_init_dict_service 回源数据库并建立正确缓存。
        await RedisCURD(redis).delete(_dict_cache_key(data.dict_type))
        log.info(f"创建字典类型成功: {new_obj_dict}")

        return new_obj_dict

    @classmethod
    async def update_obj_service(
        cls,
        auth: AuthSchema,
        redis: Redis,
        id: int,
        data: DictTypeUpdateSchema,
    ) -> dict:
        """
        更新数据字典类型

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis客户端
        - id (int): 数据字典类型ID
        - data (DictTypeUpdateSchema): 数据字典类型更新模型

        返回:
        - dict: 数据字典类型详情字典
        """
        exist_obj = await DictTypeCRUD(auth).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg="更新失败，该数据字典类型不存在")
        if exist_obj.dict_name != data.dict_name:
            raise CustomException(msg="更新失败，数据字典类型名称不可以修改")

        old_dict_type = exist_obj.dict_type

        # 如果字典类型修改或状态变更，则同步修改对应字典数据。
        if exist_obj.dict_type != data.dict_type or exist_obj.status != data.status:
            exist_obj_type_list = await DictDataCRUD(auth).list(
                search={"dict_type": exist_obj.dict_type}
            )
            if exist_obj_type_list:
                for item in exist_obj_type_list:
                    item.dict_type = data.dict_type
                    dict_data = DictDataUpdateSchema(
                        dict_sort=item.dict_sort,
                        dict_label=item.dict_label,
                        dict_value=item.dict_value,
                        dict_type=data.dict_type,
                        dict_type_id=item.dict_type_id,
                        css_class=item.css_class,
                        list_class=item.list_class,
                        is_default=item.is_default,
                        status=data.status,
                        description=item.description,
                    )
                    await DictDataCRUD(auth).update_obj_crud(id=item.id, data=dict_data)

        obj = await DictTypeCRUD(auth).update_obj_crud(id=id, data=data)

        new_obj_dict = DictTypeOutSchema.model_validate(obj).model_dump()

        # 更新成功后失效旧、新类型缓存，避免在事务内写入未提交数据。
        await RedisCURD(redis).delete(
            _dict_cache_key(old_dict_type),
            _dict_cache_key(data.dict_type),
        )
        log.info(f"更新字典类型成功并失效缓存: {new_obj_dict}")

        return new_obj_dict

    @classmethod
    async def delete_obj_service(cls, auth: AuthSchema, redis: Redis, ids: list[int]) -> None:
        """
        删除数据字典类型

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis客户端
        - ids (list[int]): 数据字典类型ID列表

        返回:
        - None
        """
        if len(ids) < 1:
            raise CustomException(msg="删除失败，删除对象不能为空")
        dict_types = set()
        for id in ids:
            exist_obj = await DictTypeCRUD(auth).get_obj_by_id_crud(id=id)
            if not exist_obj:
                raise CustomException(msg="删除失败，该数据字典类型不存在")
            # 检查是否有字典数据
            exist_obj_type_list = await DictDataCRUD(auth).list(search={"dict_type": id})
            if len(exist_obj_type_list) > 0:
                # 如果有字典数据，不能删除
                raise CustomException(msg="删除失败，该数据字典类型下存在字典数据")
            dict_types.add(exist_obj.dict_type)
        await DictTypeCRUD(auth).delete_obj_crud(ids=ids)
        await RedisCURD(redis).delete(*[_dict_cache_key(dict_type) for dict_type in dict_types])
        log.info(f"删除字典类型成功: {ids}")

    @classmethod
    async def set_obj_available_service(
        cls, auth: AuthSchema, redis: Redis, data: BatchSetAvailable
    ) -> None:
        """
        设置数据字典类型状态

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (BatchSetAvailable): 批量设置状态模型

        返回:
        - None
        """
        dict_types = set()
        for id in data.ids:
            obj = await DictTypeCRUD(auth).get_obj_by_id_crud(id=id)
            if obj:
                dict_types.add(obj.dict_type)

        await DictTypeCRUD(auth).set_obj_available_crud(ids=data.ids, status=data.status)
        await RedisCURD(redis).delete(*[_dict_cache_key(dict_type) for dict_type in dict_types])

    @classmethod
    async def export_obj_service(cls, data_list: list[dict]) -> bytes:
        """
        导出数据字典类型列表

        参数:
        - data_list (list[dict]): 数据字典类型列表

        返回:
        - bytes: Excel文件字节流
        """
        mapping_dict = {
            "id": "编号",
            "dict_name": "字典名称",
            "dict_type": "字典类型",
            "status": "状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
            "created_id": "创建者ID",
            "updated_id": "更新者ID",
        }

        # 复制数据并转换状态
        data = data_list.copy()
        for item in data:
            # 处理状态
            item["status"] = "启用" if item.get("status") == "0" else "停用"
            item["creator"] = (
                item.get("creator", {}).get("name", "未知")
                if isinstance(item.get("creator"), dict)
                else "未知"
            )

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)


class DictDataService:
    """
    字典数据管理模块服务层
    """

    @classmethod
    async def _invalidate_cache(cls, redis: Redis, *dict_types: str) -> None:
        """失效指定字典类型缓存；缓存异常不影响数据库业务。"""
        keys = [_dict_cache_key(dict_type) for dict_type in set(dict_types) if dict_type]
        if not keys:
            return
        if not await RedisCURD(redis).delete(*keys):
            log.warning(f"失效字典缓存失败: {keys}")

    @classmethod
    async def _set_cache(
        cls, redis: Redis, dict_type: str, items: list[dict]
    ) -> None:
        """写入启用字典项缓存。"""
        if not await RedisCURD(redis).set_json(
            key=_dict_cache_key(dict_type),
            value=items,
            expire=settings.DICT_CACHE_EXPIRE_SECONDS,
        ):
            log.warning(f"写入字典缓存失败: {dict_type}")

    @classmethod
    async def get_obj_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        获取数据字典数据详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 数据字典数据ID

        返回:
        - dict: 数据字典数据详情字典
        """
        obj = await DictDataCRUD(auth).get_obj_by_id_crud(id=id)
        return DictDataOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def get_obj_list_service(
        cls,
        auth: AuthSchema,
        search: DictDataQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[dict]:
        """
        获取数据字典数据列表

        参数:
        - auth (AuthSchema): 认证信息模型
        - search (DictDataQueryParam | None): 搜索条件模型
        - order_by (list[dict] | None): 排序字段列表

        返回:
        - list[dict]: 数据字典数据详情字典列表
        """
        obj_list = await DictDataCRUD(auth).get_obj_list_crud(
            search=search.__dict__, order_by=order_by
        )
        return [DictDataOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def get_obj_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: DictDataQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> dict:
        """
        分页查询字典数据（数据库 OFFSET/LIMIT）。

        参数:
        - auth (AuthSchema): 认证信息模型
        - page_no (int): 页码（从 1 开始）
        - page_size (int): 每页条数
        - search (DictDataQueryParam | None): 查询条件
        - order_by (list[dict] | None): 排序字段列表

        返回:
        - dict: 分页结果（结构由 `CRUD.page` 返回约定）
        """
        offset = (page_no - 1) * page_size
        return await DictDataCRUD(auth).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search.__dict__ if search else {},
            out_schema=DictDataOutSchema,
        )

    @classmethod
    async def init_dict_service(cls, redis: Redis) -> None:
        """
        应用初始化: 获取所有字典类型对应的字典数据信息并按租户缓存。

        参数:
        - redis (Redis): Redis客户端

        返回:
        - None
        """
        try:
            async with async_db_session() as session:
                async with session.begin():
                    auth = AuthSchema(db=session, check_data_scope=False)
                    obj_list = await DictTypeCRUD(auth).get_obj_list_crud()
                    if not obj_list:
                        log.warning("未找到任何字典类型数据")
                        return

                    for obj in obj_list:
                        dict_type = obj.dict_type
                        redis_key = _dict_cache_key(dict_type)

                        try:
                            # 停用的字典类型不应继续保留可被前端读取的缓存。
                            if obj.status != "0":
                                await RedisCURD(redis).delete(redis_key)
                                continue

                            dict_data_list = await DictDataCRUD(auth).get_obj_list_crud(
                                search={"dict_type": dict_type, "status": "0"},
                                order_by=[{"dict_sort": "asc"}, {"id": "asc"}],
                            )
                            dict_data = [
                                DictDataOutSchema.model_validate(row).model_dump(mode="json")
                                for row in dict_data_list
                                if row
                            ]
                            await cls._set_cache(
                                redis=redis, dict_type=dict_type, items=dict_data
                            )
                        except Exception as e:
                            log.error(f"❌ 初始化字典数据失败 [{dict_type}]: {e}")

        except Exception as e:
            log.error(f"字典初始化过程发生错误: {e}")
            raise CustomException(msg=f"字典数据初始化失败: {e!s}")

    @classmethod
    async def get_init_dict_service(cls, redis: Redis, dict_type: str) -> list[dict]:
        """
        获取启用的字典数据列表信息。

        优先从 Redis 读取，缓存未命中或格式异常时回源数据库。
        字典管理接口会在状态或内容变化后失效该缓存。

        参数:
        - redis (Redis): Redis客户端
        - dict_type (str): 字典类型

        返回:
        - list[dict]: 字典数据列表
        """
        redis_key = _dict_cache_key(dict_type)
        cached = _active_dict_cache_items(await RedisCURD(redis).get_json(redis_key))
        if cached is not None:
            return cached

        try:
            async with async_db_session() as session:
                async with session.begin():
                    auth = AuthSchema(db=session, check_data_scope=False)
                    dict_type_obj = await DictTypeCRUD(auth).get(dict_type=dict_type)
                    if not dict_type_obj:
                        raise CustomException(msg="数据字典不存在")

                    if dict_type_obj.status != "0":
                        await RedisCURD(redis).delete(redis_key)
                        return []

                    dict_data_list = await DictDataCRUD(auth).get_obj_list_crud(
                        search={"dict_type": dict_type, "status": "0"},
                        order_by=[{"dict_sort": "asc"}, {"id": "asc"}],
                    )
                    result = [
                        DictDataOutSchema.model_validate(row).model_dump(mode="json")
                        for row in dict_data_list
                        if row
                    ]

            # 数据库是缓存未命中时的权威来源，查询结果回写 Redis。
            await cls._set_cache(redis=redis, dict_type=dict_type, items=result)

            return result
        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取启用字典数据失败: {e!s}")
            raise CustomException(msg=f"获取字典数据失败: {e!s}")

    @classmethod
    async def create_obj_service(
        cls, auth: AuthSchema, redis: Redis, data: DictDataCreateSchema
    ) -> dict:
        """
        创建数据字典数据

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis客户端
        - data (DictDataCreateSchema): 数据字典数据创建模型

        返回:
        - dict: 数据字典数据详情字典
        """
        # 检查相同字典类型下dict_label是否已存在
        exist_label_obj = await DictDataCRUD(auth).get(
            dict_type=data.dict_type, dict_label=data.dict_label
        )
        if exist_label_obj:
            raise CustomException(msg=f'创建失败，该字典类型下的字典标签"{data.dict_label}"已存在')

        # 检查相同字典类型下dict_value是否已存在
        exist_value_obj = await DictDataCRUD(auth).get(
            dict_type=data.dict_type, dict_value=data.dict_value
        )
        if exist_value_obj:
            raise CustomException(msg=f'创建失败，该字典类型下的字典键值"{data.dict_value}"已存在')

        obj = await DictDataCRUD(auth).create_obj_crud(data=data)

        # 数据库变更成功后让下次读取从数据库重建缓存，避免在事务提交前
        # 把未提交的数据写入 Redis。
        await cls._invalidate_cache(redis, data.dict_type)
        log.info(f"创建字典数据成功并失效缓存: {obj}")

        return DictDataOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def update_obj_service(
        cls,
        auth: AuthSchema,
        redis: Redis,
        id: int,
        data: DictDataUpdateSchema,
    ) -> dict:
        """
        更新数据字典数据

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis客户端
        - id (int): 数据字典数据ID
        - data (DictDataUpdateSchema): 数据字典数据更新模型

        返回:
        - Dict: 数据字典数据详情字典
        """
        exist_obj = await DictDataCRUD(auth).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg="更新失败，该字典数据不存在")

        # 检查相同字典类型下dict_label是否已存在（排除当前记录）
        if exist_obj.dict_label != data.dict_label:
            exist_label_obj = await DictDataCRUD(auth).get(
                dict_type=data.dict_type, dict_label=data.dict_label
            )
            if exist_label_obj:
                raise CustomException(
                    msg=f'更新失败，该字典类型下的字典标签"{data.dict_label}"已存在'
                )

        # 检查相同字典类型下dict_value是否已存在（排除当前记录）
        if exist_obj.dict_value != data.dict_value:
            exist_value_obj = await DictDataCRUD(auth).get(
                dict_type=data.dict_type, dict_value=data.dict_value
            )
            if exist_value_obj:
                raise CustomException(
                    msg=f'更新失败，该字典类型下的字典键值"{data.dict_value}"已存在'
                )

        old_dict_type = exist_obj.dict_type

        obj = await DictDataCRUD(auth).update_obj_crud(id=id, data=data)
        await cls._invalidate_cache(redis, old_dict_type, data.dict_type)
        log.info(f"更新字典数据成功并失效缓存: {obj}")

        return DictDataOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def delete_obj_service(cls, auth: AuthSchema, redis: Redis, ids: list[int]) -> None:
        """
        删除数据字典数据

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis客户端
        - ids (list[int]): 数据字典数据ID列表

        返回:
        - None
        """
        try:
            if len(ids) < 1:
                raise CustomException(msg="删除失败，删除对象不能为空")

            # 首先检查是否包含系统默认数据
            for id in ids:
                exist_obj = await DictDataCRUD(auth).get_obj_by_id_crud(id=id)
                if not exist_obj:
                    raise CustomException(msg=f"{id} 删除失败，该字典数据不存在")
                # 系统默认字典数据不允许删除
                if exist_obj.is_default:
                    raise CustomException(msg=f"删除失败，ID为{id}的系统默认字典数据不允许删除")

            # 获取所有需要清除的缓存键
            dict_types_to_clear = set()
            for id in ids:
                exist_obj = await DictDataCRUD(auth).get_obj_by_id_crud(id=id)
                if exist_obj:
                    dict_types_to_clear.add(exist_obj.dict_type)

            # 执行删除操作
            await DictDataCRUD(auth).delete_obj_crud(ids=ids)

            # 清除缓存
            for dict_type in dict_types_to_clear:
                try:
                    await cls._invalidate_cache(redis, dict_type)
                    log.info(f"清除字典缓存成功: {dict_type}")
                except Exception as e:
                    log.warning(f"清除字典缓存失败: {e}")
                    # 缓存清除失败不影响删除操作

            log.info(f"删除字典数据成功，ID列表: {ids}")

        except CustomException:
            raise
        except Exception as e:
            log.error(f"删除字典数据失败: {e!s}")
            raise CustomException(msg=f"删除字典数据失败: {e!s}")

    @classmethod
    async def set_obj_available_service(
        cls, auth: AuthSchema, redis: Redis, data: BatchSetAvailable
    ) -> None:
        """
        批量修改数据字典数据状态

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (BatchSetAvailable): 批量修改数据字典数据状态负载模型

        返回:
        - None
        """
        dict_types = set()
        for id in data.ids:
            obj = await DictDataCRUD(auth).get_obj_by_id_crud(id=id)
            if obj:
                dict_types.add(obj.dict_type)

        await DictDataCRUD(auth).set_obj_available_crud(ids=data.ids, status=data.status)
        await cls._invalidate_cache(redis, *dict_types)

    @classmethod
    async def export_obj_service(cls, data_list: list[dict]) -> bytes:
        """
        导出数据字典数据列表

        参数:
        - data_list (list[dict]): 数据字典数据列表

        返回:
        - bytes: Excel文件字节流
        """
        mapping_dict = {
            "id": "编号",
            "dict_sort": "字典排序",
            "dict_label": "字典标签",
            "dict_value": "字典键值",
            "dict_type": "字典类型",
            "css_class": "样式属性",
            "list_class": "表格回显样式",
            "is_default": "是否默认",
            "status": "状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
            "created_id": "创建者ID",
            "updated_id": "更新者ID",
        }

        # 复制数据并转换状态
        data = data_list.copy()
        for item in data:
            # 处理状态
            item["status"] = "启用" if item.get("status") == "0" else "停用"
            # 处理是否默认
            item["is_default"] = "是" if item.get("is_default") else "否"
            item["creator"] = (
                item.get("creator", {}).get("name", "未知")
                if isinstance(item.get("creator"), dict)
                else "未知"
            )

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)
