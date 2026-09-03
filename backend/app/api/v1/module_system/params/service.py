import json

from redis.asyncio.client import Redis

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.enums import RedisInitKeyConfig
from app.config.setting import settings
from app.core.database import async_db_session
from app.core.exceptions import CustomException
from app.core.logger import log
from app.core.redis_crud import RedisCURD
from app.utils.excel_util import ExcelUtil

from .crud import ParamsCRUD
from .schema import (
    ParamsCreateSchema,
    ParamsOutSchema,
    ParamsQueryParam,
    ParamsUpdateSchema,
)


_CONFIG_CACHE_PREFIX = RedisInitKeyConfig.SYSTEM_CONFIG.key
_CONFIG_LIST_CACHE_KEY = f"{_CONFIG_CACHE_PREFIX}:__all__"


def _config_cache_key(config_key: str) -> str:
    """生成单个系统配置缓存键。"""
    return f"{_CONFIG_CACHE_PREFIX}:{config_key}"


class ParamsService:
    """
    配置管理模块服务层
    """

    @classmethod
    async def _invalidate_list_cache(cls, redis: Redis) -> None:
        """失效配置列表缓存；单项缓存由调用方单独维护。"""
        if not await RedisCURD(redis).delete(_CONFIG_LIST_CACHE_KEY):
            log.warning("失效系统配置列表缓存失败")

    @classmethod
    async def _set_item_cache(cls, redis: Redis, config: dict) -> None:
        """写入单项系统配置缓存。"""
        config_key = config.get("config_key")
        if not config_key:
            return
        if not await RedisCURD(redis).set_json(
            key=_config_cache_key(config_key),
            value=config,
            expire=settings.SYSTEM_CONFIG_CACHE_EXPIRE_SECONDS,
        ):
            log.warning(f"写入系统配置缓存失败: {config_key}")

    @classmethod
    async def _set_list_cache(cls, redis: Redis, configs: list[dict]) -> None:
        """写入系统配置列表缓存。"""
        if not await RedisCURD(redis).set_json(
            key=_CONFIG_LIST_CACHE_KEY,
            value=configs,
            expire=settings.SYSTEM_CONFIG_CACHE_EXPIRE_SECONDS,
        ):
            log.warning("写入系统配置列表缓存失败")

    @classmethod
    async def get_obj_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        获取配置详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 配置管理型ID

        返回:
        - dict: 配置管理型模型实例字典表示
        """
        obj = await ParamsCRUD(auth).get_obj_by_id_crud(id=id)
        return ParamsOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def get_obj_by_key_service(cls, auth: AuthSchema, config_key: str) -> dict:
        """
        根据配置键获取配置详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - config_key (str): 配置管理型key

        返回:
        - Dict: 配置管理型模型实例字典表示
        """
        obj = await ParamsCRUD(auth).get_obj_by_key_crud(key=config_key)
        if not obj:
            raise CustomException(msg=f"配置键 {config_key} 不存在")
        return ParamsOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def get_config_value_by_key_service(cls, auth: AuthSchema, config_key: str) -> str | None:
        """
        根据配置键获取配置值

        参数:
        - auth (AuthSchema): 认证信息模型
        - config_key (str): 配置管理型key

        返回:
        - str | None: 配置值字符串或None
        """
        obj = await ParamsCRUD(auth).get_obj_by_key_crud(key=config_key)
        if not obj:
            raise CustomException(msg=f"配置键 {config_key} 不存在")
        return obj.config_value

    @classmethod
    async def get_obj_list_service(
        cls,
        auth: AuthSchema,
        search: ParamsQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[dict]:
        """
        获取配置管理型列表

        参数:
        - auth (AuthSchema): 认证信息模型
        - search (ParamsQueryParam | None): 查询参数对象
        - order_by (list[dict] | None): 排序参数列表

        返回:
        - list[dict]: 配置管理型模型实例字典列表表示
        """
        obj_list = None
        if search:
            obj_list = await ParamsCRUD(auth).get_obj_list_crud(
                search=search.__dict__, order_by=order_by
            )
        else:
            obj_list = await ParamsCRUD(auth).get_obj_list_crud()
        return [ParamsOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def get_obj_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: ParamsQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        """
        分页查询系统参数（数据库 OFFSET/LIMIT）。

        参数:
        - auth (AuthSchema): 认证信息模型
        - page_no (int): 页码（从 1 开始）
        - page_size (int): 每页条数
        - search (ParamsQueryParam | None): 查询条件
        - order_by (list[dict[str, str]] | None): 排序字段列表

        返回:
        - dict: 分页结果（结构由 `CRUD.page` 返回约定）
        """
        offset = (page_no - 1) * page_size
        return await ParamsCRUD(auth).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search.__dict__ if search else {},
            out_schema=ParamsOutSchema,
        )

    @classmethod
    async def create_obj_service(
        cls, auth: AuthSchema, redis: Redis, data: ParamsCreateSchema
    ) -> dict:
        """
        创建配置管理型

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis 客户端实例
        - data (ParamsCreateSchema): 配置管理型创建模型

        返回:
        - dict: 新创建的配置管理型模型实例字典表示
        """
        exist_obj = await ParamsCRUD(auth).get(config_key=data.config_key)
        if exist_obj:
            raise CustomException(msg="创建失败，该配置key已存在")
        obj = await ParamsCRUD(auth).create_obj_crud(data=data)

        new_obj_dict = ParamsOutSchema.model_validate(obj).model_dump()

        # 只失效缓存，避免在数据库事务提交前把未提交数据写入 Redis。
        await RedisCURD(redis).delete(_config_cache_key(data.config_key))
        await cls._invalidate_list_cache(redis)

        return new_obj_dict

    @classmethod
    async def update_obj_service(
        cls, auth: AuthSchema, redis: Redis, id: int, data: ParamsUpdateSchema
    ) -> dict:
        """
        更新配置管理型

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis 客户端实例
        - id (int): 配置管理型ID
        - data (ParamsUpdateSchema): 配置管理型更新模型

        返回:
        - Dict: 更新后的配置管理型模型实例字典表示
        """
        exist_obj = await ParamsCRUD(auth).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg="更新失败，该数系统配置不存在")
        if exist_obj.config_key != data.config_key:
            raise CustomException(msg="更新失败，系统配置key不允许修改")

        new_obj = await ParamsCRUD(auth).update_obj_crud(id=id, data=data)
        if not new_obj:
            raise CustomException(msg="更新失败，系统配置不存在")
        out = ParamsOutSchema.model_validate(new_obj)
        new_obj_dict = out.model_dump()

        # 只失效缓存，下一次读取会从数据库重建最新值。
        await RedisCURD(redis).delete(_config_cache_key(new_obj.config_key))
        await cls._invalidate_list_cache(redis)

        return new_obj_dict

    @classmethod
    async def delete_obj_service(cls, auth: AuthSchema, redis: Redis, ids: list[int]) -> None:
        """
        删除配置管理型

        参数:
        - auth (AuthSchema): 认证信息模型
        - redis (Redis): Redis 客户端实例
        - ids (list[int]): 配置管理型ID列表

        返回:
        - None
        """
        if len(ids) < 1:
            raise CustomException(msg="删除失败，删除对象不能为空")
        for id in ids:
            exist_obj = await ParamsCRUD(auth).get_obj_by_id_crud(id=id)
            if not exist_obj:
                raise CustomException(msg="删除失败，该数据字典类型不存在")
            # 检查是否是否初始化类型
            if exist_obj.config_type:
                # 如果有字典数据，不能删除
                raise CustomException(
                    msg=f"{exist_obj.config_name} 删除失败，系统初始化配置不可以删除"
                )

        # 软删除后对象可能无法再次查询，因此必须提前保存配置 key。
        config_keys = []
        for id in ids:
            exist_obj = await ParamsCRUD(auth).get_obj_by_id_crud(id=id)
            if exist_obj:
                config_keys.append(exist_obj.config_key)

        await ParamsCRUD(auth).delete_obj_crud(ids=ids)

        if config_keys:
            await RedisCURD(redis).delete(*[_config_cache_key(key) for key in config_keys])
        await cls._invalidate_list_cache(redis)
        log.info(f"删除系统配置成功: {ids}")

    @classmethod
    async def export_obj_service(cls, data_list: list[dict]) -> bytes:
        """
        导出系统配置列表

        参数:
        - data_list (list[dict]): 系统配置模型实例字典列表表示

        返回:
        - bytes: Excel文件二进制数据
        """
        mapping_dict = {
            "id": "编号",
            "config_name": "参数名称",
            "config_key": "参数键名",
            "config_value": "参数键值",
            "config_type": "系统内置((True:是 False:否))",
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
            item["config_type"] = "是" if item.get("config_type") else "否"
            item["creator"] = (
                item.get("creator", {}).get("name", "未知")
                if isinstance(item.get("creator"), dict)
                else "未知"
            )

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)

    @classmethod
    async def init_config_service(cls, redis: Redis) -> None:
        """
        初始化系统配置并按租户缓存。

        参数:
        - redis (Redis): Redis 客户端实例

        返回:
        - None
        """
        async with async_db_session() as session:
            async with session.begin():
                auth = AuthSchema(db=session, check_data_scope=False)
                config_obj = await ParamsCRUD(auth).get_obj_list_crud()
                if not config_obj:
                    raise CustomException(msg="系统配置不存在")
                configs = [
                    ParamsOutSchema.model_validate(config).model_dump(mode="json")
                    for config in config_obj
                ]

        for config in configs:
            await cls._set_item_cache(redis=redis, config=config)
        await cls._set_list_cache(redis=redis, configs=configs)

    @classmethod
    async def get_init_config_service(cls, redis: Redis) -> list[dict]:
        """
        获取系统配置

        参数:
        - redis (Redis): Redis 客户端实例


        返回:
        - list[dict]: 系统配置模型实例字典列表表示
        """
        cached = await RedisCURD(redis).get_json(_CONFIG_LIST_CACHE_KEY)
        if isinstance(cached, list):
            return [item for item in cached if isinstance(item, dict)]

        log.info("Redis 中没有有效的系统配置列表，从数据库中加载")
        async with async_db_session() as session:
            async with session.begin():
                auth = AuthSchema(db=session, check_data_scope=False)
                config_obj = await ParamsCRUD(auth).get_obj_list_crud()
                configs = [
                    ParamsOutSchema.model_validate(config).model_dump(mode="json")
                    for config in config_obj
                ]

        for config in configs:
            await cls._set_item_cache(redis=redis, config=config)
        await cls._set_list_cache(redis=redis, configs=configs)
        return configs

    @classmethod
    async def get_system_config_for_middleware(cls, redis: Redis) -> dict:
        """
        获取中间件所需的系统配置

        参数:
        - redis (Redis): Redis 客户端实例

        返回:
        - dict: 包含演示模式、IP白名单、API白名单和IP黑名单的配置字典
        """
        # 初始化默认配置
        config_result = {
            "demo_enable": False,
            "ip_white_list": [],
            "white_api_list_path": [],
            "ip_black_list": [],
        }

        configs = await cls.get_init_config_service(redis=redis)
        config_map = {
            item.get("config_key"): item
            for item in configs
            if isinstance(item, dict) and item.get("status") == "0"
        }

        # 配置值在数据库中以字符串保存，按目标类型安全转换。
        demo_config = config_map.get("demo_enable", {})
        demo_value = demo_config.get("config_value") if isinstance(demo_config, dict) else None
        if isinstance(demo_value, str):
            config_result["demo_enable"] = demo_value.strip().lower() == "true"
        elif isinstance(demo_value, bool):
            config_result["demo_enable"] = demo_value

        for config_key, result_key in (
            ("ip_white_list", "ip_white_list"),
            ("white_api_list_path", "white_api_list_path"),
            ("ip_black_list", "ip_black_list"),
        ):
            config = config_map.get(config_key, {})
            raw_value = config.get("config_value") if isinstance(config, dict) else None
            if not raw_value:
                continue
            try:
                value = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
                if isinstance(value, list):
                    config_result[result_key] = value
            except (TypeError, ValueError):
                log.warning(f"解析系统配置失败: {config_key}")
        return config_result
