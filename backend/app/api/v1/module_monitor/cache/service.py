from redis.asyncio.client import Redis

from app.common.enums import RedisInitKeyConfig
from app.core.exceptions import CustomException
from app.core.redis_crud import RedisCURD

from .schema import CacheInfoSchema, CacheMonitorSchema


class CacheService:
    """
    缓存监控模块服务层
    """

    @staticmethod
    def _validate_cache_name(cache_name: str) -> str:
        """只允许访问系统登记的缓存命名空间。"""
        allowed_names = {item.key for item in RedisInitKeyConfig}
        if cache_name not in allowed_names:
            raise CustomException(msg="不支持的缓存命名空间")
        return cache_name

    @classmethod
    async def get_cache_monitor_statistical_info_service(cls, redis: Redis) -> dict:
        """
        获取缓存监控信息。

        参数:
        - redis (Redis): Redis 对象。

        返回:
        - dict: 缓存监控信息字典。
        """
        info = await RedisCURD(redis).info()
        db_size = await RedisCURD(redis).db_size()
        command_stats_dict = await RedisCURD(redis).commandstats()

        command_stats = sorted(
            [
                {
                    "name": key.removeprefix("cmdstat_"),
                    "value": str(value.get("calls", 0)),
                }
                for key, value in command_stats_dict.items()
                if key.startswith("cmdstat_") and isinstance(value, dict)
            ],
            key=lambda item: int(item["value"]),
            reverse=True,
        )
        result = CacheMonitorSchema(command_stats=command_stats, db_size=db_size, info=info)

        return result.model_dump()

    @classmethod
    async def get_cache_monitor_cache_name_service(cls) -> list:
        """
        获取缓存名称列表信息。

        返回:
        - list: 缓存名称列表信息。
        """
        name_list = [
            CacheInfoSchema(
                cache_key="",
                cache_name=key_config.key,
                cache_value="",
                remark=key_config.remark,
            ).model_dump()
            for key_config in RedisInitKeyConfig
        ]

        return name_list

    @classmethod
    async def get_cache_monitor_cache_key_service(cls, redis: Redis, cache_name: str) -> list:
        """
        获取缓存键名列表信息。

        参数:
        - redis (Redis): Redis 对象。
        - cache_name (str): 缓存名称。

        返回:
        - list: 缓存键名列表信息。
        """
        cache_name = cls._validate_cache_name(cache_name)
        cache_keys = await RedisCURD(redis).get_keys(f"{cache_name}:*")
        cache_key_list = [
            key[len(cache_name) + 1 :]
            for key in cache_keys
            if key.startswith(f"{cache_name}:")
        ]

        return sorted(cache_key_list)

    @classmethod
    async def get_cache_monitor_cache_value_service(
        cls, redis: Redis, cache_name: str, cache_key: str
    ) -> dict:
        """
        获取缓存内容信息。

        参数:
        - redis (Redis): Redis 对象。
        - cache_name (str): 缓存名称。
        - cache_key (str): 缓存键名。

        返回:
        - dict: 缓存内容信息字典。
        """
        cache_name = cls._validate_cache_name(cache_name)
        cache_value = await RedisCURD(redis).get(f"{cache_name}:{cache_key}")

        return CacheInfoSchema(
            cache_key=cache_key,
            cache_name=cache_name,
            cache_value=cache_value,
            remark="",
        ).model_dump()

    @classmethod
    async def clear_cache_monitor_cache_name_service(cls, redis: Redis, cache_name: str) -> bool:
        """
        清除指定缓存名称对应的所有键值。

        参数:
        - redis (Redis): Redis 对象。
        - cache_name (str): 缓存名称。

        返回:
        - bool: 是否清理成功。
        """
        cache_name = cls._validate_cache_name(cache_name)
        cache_keys = await RedisCURD(redis).get_keys(f"{cache_name}:*")
        if cache_keys:
            await RedisCURD(redis).delete(*cache_keys)

        return True

    @classmethod
    async def clear_cache_monitor_cache_key_service(
        cls, redis: Redis, cache_name: str, cache_key: str
    ) -> bool:
        """
        清除匹配指定键名的所有键值。

        参数:
        - redis (Redis): Redis 对象。
        - cache_name (str): 缓存名称。
        - cache_key (str): 缓存名称下的键名。

        返回:
        - bool: 是否清理成功。
        """
        if not cache_name or not cache_key:
            return False
        cache_name = cls._validate_cache_name(cache_name)
        return await RedisCURD(redis).delete(f"{cache_name}:{cache_key}")

    @classmethod
    async def clear_cache_monitor_all_service(cls, redis: Redis) -> bool:
        """
        清除所有缓存。

        参数:
        - redis (Redis): Redis 对象。

        返回:
        - bool: 是否清理成功。
        """
        cache_keys: list[str] = []
        for key_config in RedisInitKeyConfig:
            cache_keys.extend(
                await RedisCURD(redis).get_keys(f"{key_config.key}:*")
            )
        if cache_keys:
            await RedisCURD(redis).delete(*sorted(set(cache_keys)))

        return True
