import json
from collections.abc import AsyncGenerator

from fastapi import Depends, Query, Request
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.user.crud import UserCRUD
from app.api.v1.module_system.user.model import UserModel
from app.common.enums import RedisInitKeyConfig
from app.config.setting import settings
from app.core.database import async_db_session
from app.core.exceptions import CustomException
from app.core.logger import log
from app.core.redis_crud import RedisCURD
from app.core.security import OAuth2Schema, decode_access_token


# ---------------------------------------------------------------------------
# Database / Redis
# ---------------------------------------------------------------------------


async def db_getter_read() -> AsyncGenerator[AsyncSession, None]:
    """只读数据库会话。适用于纯 SELECT 查询。"""
    async with async_db_session() as session:
        yield session


async def db_getter() -> AsyncGenerator[AsyncSession, None]:
    """读写数据库会话。适用于 INSERT / UPDATE / DELETE。"""
    async with async_db_session() as session:
        async with session.begin():
            yield session


async def redis_getter(request: Request) -> Redis:
    """获取应用级 Redis 连接。"""
    return request.app.state.redis


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _normalize_token(token: str | None) -> str:
    """统一处理 OAuth2 Bearer Token。"""
    if not token:
        raise CustomException(
            msg="认证已失效",
            code=10401,
            status_code=401,
        )

    token = token.strip()

    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    if not token:
        raise CustomException(
            msg="认证已失效",
            code=10401,
            status_code=401,
        )

    return token


def _load_token_user_info(payload) -> dict:
    """从 JWT sub 中取得会话信息。"""
    if not payload or getattr(payload, "is_refresh", False):
        raise CustomException(
            msg="非法凭证",
            code=10401,
            status_code=401,
        )

    online_user_info = payload.sub

    try:
        if isinstance(online_user_info, dict):
            user_info = online_user_info
        else:
            user_info = json.loads(online_user_info)
    except (TypeError, json.JSONDecodeError):
        raise CustomException(
            msg="认证信息无效，请重新登录",
            code=10401,
            status_code=401,
        )

    if not isinstance(user_info, dict):
        raise CustomException(
            msg="认证信息无效，请重新登录",
            code=10401,
            status_code=401,
        )

    return user_info


async def _verify_redis_access_token(
    redis: Redis,
    session_id: str,
    token: str,
) -> None:
    """
    验证 Redis 中的 Access Token。

    不仅检查 key 是否存在，还必须检查 Redis 保存的 token
    与当前请求携带的 token 完全一致。

    这样可以保证：
    1. logout 后旧 token 立即失效；
    2. refresh 后旧 access_token 立即失效；
    3. 同一个 session 只允许 Redis 当前保存的 access_token 访问。
    """
    redis_key = f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}"

    stored_token = await RedisCURD(redis).get(redis_key)

    if not stored_token:
        raise CustomException(
            msg="认证已失效",
            code=10401,
            status_code=401,
        )

    if isinstance(stored_token, bytes):
        stored_token = stored_token.decode("utf-8")

    if stored_token != token:
        raise CustomException(
            msg="认证已失效，请重新登录",
            code=10401,
            status_code=401,
        )


async def _sliding_access_token(
    redis: Redis,
    session_id: str,
) -> None:
    """
    Access Token 滑动过期。

    注意：
    Refresh Token 不在这里续期。

    Access Token：
        每次成功访问接口后重新获得完整的 access TTL。

    Refresh Token：
        生命周期固定，由登录 / refresh 时设置，
        不因为普通 API 请求而延长。
    """
    #
    if not settings.TOKEN_SLIDING_EXPIRE:
        return

    await RedisCURD(redis).expire(
        key=f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}",
        expire=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )


async def _load_current_user(
    db: AsyncSession,
    user_info: dict,
) -> AuthSchema:
    """根据 JWT 中的用户名加载完整用户对象。"""
    username = user_info.get("user_name")

    if not username:
        raise CustomException(
            msg="认证已失效",
            code=10401,
            status_code=401,
        )

    auth = AuthSchema(
        db=db,
        check_data_scope=False,
    )

    user = await UserCRUD(auth).get_by_username_crud(
        username=username,
        preload=[
            "dept",
            selectinload(UserModel.roles),
            "positions",
            "created_by",
        ],
    )

    if not user:
        raise CustomException(
            msg="用户不存在",
            code=10401,
            status_code=401,
        )

    if user.status == "1":
        raise CustomException(
            msg="用户已被停用",
            code=10401,
            status_code=401,
        )

    # 只保留当前启用的角色和职位。
    if hasattr(user, "roles"):
        user.roles = [
            role
            for role in user.roles
            if role and role.status == "0"
        ]

    if hasattr(user, "positions"):
        user.positions = [
            position
            for position in user.positions
            if position and position.status == "0"
        ]

    auth.user = user
    return auth


async def _verify_token(
    token: str,
    db: AsyncSession,
    redis: Redis,
    request: Request | None = None,
) -> AuthSchema:
    """
    统一验证 Access Token。

    验证链：

        Bearer Token
            ↓
        JWT 签名 / exp
            ↓
        必须是 Access Token
            ↓
        解析 session_id
            ↓
        Redis 中必须存在当前 Access Token
            ↓
        Redis Token 必须与请求 Token 完全一致
            ↓
        Access Token 滑动续期
            ↓
        查询数据库用户
            ↓
        用户必须存在且启用
    """
    token = _normalize_token(token)

    # JWT 本身负责：
    # - SECRET_KEY
    # - algorithm
    # - exp
    # - is_refresh
    payload = decode_access_token(token)

    user_info = _load_token_user_info(payload)

    session_id = user_info.get("session_id")

    if not session_id:
        raise CustomException(
            msg="认证已失效",
            code=10401,
            status_code=401,
        )

    # Redis 负责真正的会话状态控制。
    await _verify_redis_access_token(
        redis=redis,
        session_id=session_id,
        token=token,
    )

    # 只续 Access Token。
    await _sliding_access_token(
        redis=redis,
        session_id=session_id,
    )

    auth = await _load_current_user(
        db=db,
        user_info=user_info,
    )

    if request is not None:
        request.scope["user_id"] = auth.user.id
        request.scope["user_username"] = auth.user.username
        request.scope["session_id"] = session_id

    return auth


# ---------------------------------------------------------------------------
# HTTP authentication
# ---------------------------------------------------------------------------


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(db_getter),
    redis: Redis = Depends(redis_getter),
    token: str = Depends(OAuth2Schema),
) -> AuthSchema:
    """
    获取当前登录用户。

    只接受 Access Token。

    注意：
    /auth/token/refresh 不能依赖本函数，
    因为 Access Token 过期以后，本函数本身就会返回 401。
    Refresh Token 应由 refresh service 自己验证。
    """
    return await _verify_token(
        token=token,
        db=db,
        redis=redis,
        request=request,
    )


# ---------------------------------------------------------------------------
# WebSocket authentication
# ---------------------------------------------------------------------------


async def get_current_user_ws(
    token: str = Query(..., description="认证token"),
    db: AsyncSession = Depends(db_getter),
    redis: Redis = Depends(redis_getter),
) -> AuthSchema:
    """WebSocket 专用认证，从 query 参数获取 Access Token。"""
    return await _verify_token(
        token=token,
        db=db,
        redis=redis,
    )


# ---------------------------------------------------------------------------
# Permission
# ---------------------------------------------------------------------------


class AuthPermission:
    """权限验证类。"""

    def __init__(
        self,
        permissions: list[str] | None = None,
        check_data_scope: bool = True,
    ) -> None:
        self.permissions = permissions or []
        self.check_data_scope = check_data_scope

    async def __call__(
        self,
        auth: AuthSchema = Depends(get_current_user),
    ) -> AuthSchema:
        auth.check_data_scope = self.check_data_scope

        # 超级管理员直接通过。
        if auth.user and auth.user.is_superuser:
            return auth

        # 当前接口没有声明权限要求。
        if not self.permissions:
            return auth

        # 通配权限。
        if "*" in self.permissions or "*:*:*" in self.permissions:
            return auth

        # 用户没有角色。
        if not auth.user or not auth.user.roles:
            raise CustomException(
                msg="无权限操作",
                code=10403,
                status_code=403,
            )

        user_permissions = {
            menu.permission
            for role in auth.user.roles
            if role.status == "0"
            for menu in role.menus
            if menu.permission and menu.status == "0"
        }

        # 满足任意一个权限即可。
        if not any(
            permission in user_permissions
            for permission in self.permissions
        ):
            log.error(
                f"用户缺少任何所需的权限: {self.permissions}"
            )
            raise CustomException(
                msg="无权限操作",
                code=10403,
                status_code=403,
            )

        return auth