import json
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import NewType

from fastapi import Request
from redis.asyncio.client import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse

from app.api.v1.module_monitor.online.schema import OnlineOutSchema
from app.api.v1.module_system.user.crud import UserCRUD
from app.api.v1.module_system.user.model import UserModel
from app.common.enums import RedisInitKeyConfig
from app.config.setting import settings
from app.core.exceptions import CustomException
from app.core.logger import log
from app.core.redis_crud import RedisCURD
from app.core.security import (
    CustomOAuth2PasswordRequestForm,
    create_access_token,
    decode_access_token,
)
from app.utils.captcha_util import CaptchaUtil
from app.utils.common_util import get_random_character
from app.utils.hash_bcrpy_util import PwdUtil
from app.utils.ip_local_util import IpLocalUtil
from app.utils.time_util import BEIJING_TIMEZONE, now_beijing

from .schema import (
    AuthSchema,
    AutoLoginTokenSchema,
    AutoLoginUserSchema,
    CaptchaOutSchema,
    JWTOutSchema,
    JWTPayloadSchema,
    LoginResponseSchema,
    RefreshTokenPayloadSchema,
    LogoutPayloadSchema,
)


CaptchaKey = NewType("CaptchaKey", str)
CaptchaBase64 = NewType("CaptchaBase64", str)


class LoginService:
    """登录认证服务。"""

    # ==================================================================
    # 登录
    # ==================================================================

    @classmethod
    async def authenticate_user_service(
        cls,
        request: Request,
        redis: Redis,
        login_form: CustomOAuth2PasswordRequestForm,
        db: AsyncSession,
    ) -> LoginResponseSchema:
        """
        用户登录认证。

        登录流程：

            用户名密码
                ↓
            验证码
                ↓
            查询用户
                ↓
            密码校验
                ↓
            用户状态
                ↓
            创建 Access Token
                ↓
            创建 Refresh Token
                ↓
            Redis 保存会话
        """

        start_time = time.time()

        # ============================================================
        # 1. 判断是否来自 Swagger / ReDoc
        # ============================================================

        referer = request.headers.get(
            "referer",
            "",
        )

        request_from_docs = referer.endswith(
            ("docs", "redoc")
        )

        # ============================================================
        # 2. 验证码
        # ============================================================

        if (
            settings.CAPTCHA_ENABLE
            and not request_from_docs
        ):
            if (
                not login_form.captcha_key
                or not login_form.captcha
            ):
                raise CustomException(
                    msg="验证码不能为空"
                )

            await CaptchaService.check_captcha_service(
                redis=redis,
                key=login_form.captcha_key,
                captcha=login_form.captcha,
            )

        log.info(
            f"[登录计时] 验证码校验: "
            f"{round((time.time() - start_time) * 1000, 1)}ms"
        )

        # ============================================================
        # 3. 查询用户
        # ============================================================

        auth = AuthSchema(
            db=db,
            check_data_scope=False,
        )

        user = await UserCRUD(auth).get_by_username_crud(
            username=login_form.username
        )

        if not user:
            raise CustomException(
                msg="用户不存在"
            )

        log.info(
            f"[登录计时] 数据库查询用户: "
            f"{round((time.time() - start_time) * 1000, 1)}ms"
        )

        # ============================================================
        # 4. 密码校验
        # ============================================================

        if not PwdUtil.verify_password(
            plain_password=login_form.password,
            password_hash=user.password,
        ):
            raise CustomException(
                msg="账号或密码错误"
            )

        # ============================================================
        # 5. 用户状态
        # ============================================================

        if user.status == "1":
            raise CustomException(
                msg="用户已被停用"
            )

        # ============================================================
        # 6. 更新最后登录时间
        # ============================================================

        user = await UserCRUD(auth).update_last_login_crud(
            id=user.id
        )

        if not user:
            raise CustomException(
                msg="用户不存在"
            )

        # ============================================================
        # 7. 登录类型
        #
        # Swagger OAuth2 Password Flow 不会自动提交 login_type。
        #
        # 因此：
        #   普通前端登录 -> 使用前端传入的 login_type
        #   Swagger 登录  -> 默认 PC端
        # ============================================================

        login_type = (
            login_form.login_type
            or "PC端"
        )

        # ============================================================
        # 8. 创建 Token
        # ============================================================

        token = await cls.create_token_service(
            request=request,
            redis=redis,
            user=user,
            login_type=login_type,
        )

        log.info(
            f"[登录计时] 创建Token: "
            f"{round((time.time() - start_time) * 1000, 1)}ms"
        )

        # ============================================================
        # 9. 用户基本信息
        # ============================================================

        user_info = {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "avatar": user.avatar,
            "is_super_admin": user.is_superuser,
        }

        log.info(
            f"[登录计时] ⭐ 登录总耗时: "
            f"{round((time.time() - start_time) * 1000, 1)}ms"
        )

        return LoginResponseSchema(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            expires_in=token.expires_in,
            token_type=token.token_type,
            user_info=user_info,
        )

    # ==================================================================
    # 创建 Token
    # ==================================================================
    @classmethod
    async def create_token_service(
            cls,
            request: Request,
            redis: Redis,
            user: UserModel,
            login_type: str,
    ) -> JWTOutSchema:
        """
        创建 Access Token + Refresh Token。

        Access Token：
            - JWT exp = Access Token 生命周期
            - Redis TTL = Access Token 生命周期
            - 后续请求可以按照滑动过期策略续期

        Refresh Token：
            - JWT exp = 固定 7 天
            - Redis TTL = 固定 7 天
            - Access Token 刷新时，不重新计算 7 天
        """

        # ============================================================
        # 1. 创建会话 ID
        # ============================================================

        session_id = str(uuid.uuid4())

        request.scope["session_id"] = session_id
        request.scope["user_username"] = user.username

        # ============================================================
        # 2. 获取客户端信息
        # ============================================================

        user_agent = parse(
            request.headers.get(
                "user-agent",
                "",
            )
        )

        x_forwarded_for = request.headers.get(
            "X-Forwarded-For"
        )

        if x_forwarded_for:
            request_ip = (
                x_forwarded_for
                .split(",")[0]
                .strip()
            )
        else:
            request_ip = (
                request.client.host
                if request.client
                else "127.0.0.1"
            )

        # ============================================================
        # 3. IP 地址解析
        # ============================================================

        login_location = (
            await IpLocalUtil.resolve_location_for_log(
                request_ip
            )
        )

        request.scope["login_location"] = login_location

        # ============================================================
        # 4. Token 生命周期
        # ============================================================

        access_ttl = settings.ACCESS_TOKEN_EXPIRE_SECONDS
        refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_SECONDS

        now = now_beijing()

        # ============================================================
        # 5. 在线会话信息
        #
        # 注意：
        # login_time 是 datetime。
        #
        # 使用 model_dump_json() 后，
        # Pydantic 会自动把 datetime 序列化成 ISO 字符串。
        #
        # 因此不会再出现：
        #
        # TypeError:
        # Object of type datetime is not JSON serializable
        # ============================================================

        session_info = OnlineOutSchema(
            session_id=session_id,
            user_id=user.id,
            is_super_admin=user.is_superuser,
            name=user.name,
            user_name=user.username,
            avatar=user.avatar,
            ipaddr=request_ip,
            login_location=login_location,
            os=user_agent.os.family,
            browser=user_agent.browser.family,
            login_time=user.last_login,
            login_type=login_type,
        ).model_dump_json()

        # ============================================================
        # 6. 创建 Access Token
        # ============================================================

        access_token = create_access_token(
            payload=JWTPayloadSchema(
                sub=session_info,
                is_refresh=False,
                exp=now + timedelta(
                    seconds=access_ttl
                ),
            )
        )

        # ============================================================
        # 7. 创建 Refresh Token
        #
        # Refresh Token 的 exp 是登录时计算出来的固定时间。
        #
        # 例如：
        #
        # 现在：
        # 2026-08-17 10:00
        #
        # refresh_ttl：
        # 604800 秒 = 7 天
        #
        # 那么：
        # exp：
        # 2026-08-24 10:00
        #
        # 后续 refresh 不会重新变成：
        # 2026-08-24 10:00 + 7 天
        # ============================================================

        refresh_expires_at = now + timedelta(
            seconds=refresh_ttl
        )

        refresh_token = create_access_token(
            payload=JWTPayloadSchema(
                sub=session_info,
                is_refresh=True,
                exp=now + timedelta(
            seconds=refresh_ttl),
            )
        )

        # ============================================================
        # 8. Redis 保存 Access Token
        # ============================================================

        access_redis_key = (
            f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:"
            f"{session_id}"
        )

        await RedisCURD(redis).set(
            key=access_redis_key,
            value=access_token,
            expire=access_ttl,
        )

        # ============================================================
        # 9. Redis 保存 Refresh Token
        # ============================================================

        refresh_redis_key = (
            f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:"
            f"{session_id}"
        )

        await RedisCURD(redis).set(
            key=refresh_redis_key,
            value=refresh_token,
            expire=refresh_ttl,
        )

        # ============================================================
        # 10. 日志
        # ============================================================

        log.info(
            f"创建Token成功: "
            f"user_id={user.id}, "
            f"session_id={session_id}, "
            f"access_ttl={access_ttl}s, "
            f"refresh_ttl={refresh_ttl}s"
        )

        # ============================================================
        # 11. 返回
        # ============================================================

        return JWTOutSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=access_ttl,
            token_type=settings.TOKEN_TYPE,
        )

    # ==================================================================
    # Refresh Token
    # ==================================================================

    @classmethod
    async def refresh_token_service(
        cls,
        db: AsyncSession,
        redis: Redis,
        request: Request,
        refresh_token: RefreshTokenPayloadSchema,
    ) -> JWTOutSchema:
        """
        使用 Refresh Token 获取新的 Access Token。

        Refresh Token 采用轮换机制：

            old refresh token
                    ↓
              JWT 验证
                    ↓
              Redis 验证
                    ↓
              查询用户
                    ↓
              创建新 Access Token
                    ↓
              创建新 Refresh Token
                    ↓
              删除旧 Token
                    ↓
              保存新 Token

        Refresh Token 的最终过期时间固定，
        refresh 操作不会把生命周期重新延长 7 天。
        """

        # ============================================================
        # 1. 获取 Refresh Token
        # ============================================================

        incoming_refresh_token = (
            refresh_token.refresh_token
        )

        if not incoming_refresh_token:
            raise CustomException(
                msg="刷新令牌不能为空",
                code=10401,
                status_code=401,
            )

        # ============================================================
        # 2. JWT 验证
        # ============================================================

        token_payload = decode_access_token(
            token=incoming_refresh_token
        )

        # Refresh 接口只能接受 Refresh Token。
        if not token_payload.is_refresh:
            raise CustomException(
                msg="非法凭证，请传入刷新令牌",
                code=10401,
                status_code=401,
            )

        # ============================================================
        # 3. 解析 session 信息
        # ============================================================

        try:
            if isinstance(
                token_payload.sub,
                dict,
            ):
                session_info = (
                    token_payload.sub
                )
            else:
                session_info = json.loads(
                    token_payload.sub
                )

        except (
            TypeError,
            json.JSONDecodeError,
        ):
            raise CustomException(
                msg="刷新令牌数据异常",
                code=10401,
                status_code=401,
            )

        if not isinstance(
            session_info,
            dict,
        ):
            raise CustomException(
                msg="刷新令牌数据异常",
                code=10401,
                status_code=401,
            )

        session_id = session_info.get(
            "session_id"
        )

        user_id = session_info.get(
            "user_id"
        )

        if not session_id or not user_id:
            raise CustomException(
                msg="非法凭证，无法获取会话信息",
                code=10401,
                status_code=401,
            )

        # ============================================================
        # 4. Redis 验证 Refresh Token
        # ============================================================

        refresh_redis_key = (
            f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:"
            f"{session_id}"
        )

        stored_refresh_token = (
            await RedisCURD(redis).get(
                refresh_redis_key
            )
        )

        if not stored_refresh_token:
            raise CustomException(
                msg="刷新令牌已失效，请重新登录",
                code=10401,
                status_code=401,
            )

        if isinstance(
            stored_refresh_token,
            bytes,
        ):
            stored_refresh_token = (
                stored_refresh_token.decode(
                    "utf-8"
                )
            )

        # ============================================================
        # 5. Token 必须完全一致
        # ============================================================

        if not secrets.compare_digest(
            str(stored_refresh_token),
            incoming_refresh_token,
        ):
            raise CustomException(
                msg="刷新令牌已失效，请重新登录",
                code=10401,
                status_code=401,
            )

        # ============================================================
        # 6. 查询用户
        # ============================================================

        auth = AuthSchema(
            db=db,
            check_data_scope=False,
        )

        user = await UserCRUD(auth).get_by_id_crud(
            id=user_id
        )

        if not user:
            raise CustomException(
                msg="刷新Token失败，用户不存在",
                code=10401,
                status_code=401,
            )

        if user.status == "1":
            raise CustomException(
                msg="用户已被停用",
                code=10401,
                status_code=401,
            )

        # ============================================================
        # 7. 计算 Refresh Token 剩余生命周期
        #
        # 不重新给 7 天。
        # ============================================================

        refresh_exp_timestamp = (
            token_payload.exp
        )

        if not refresh_exp_timestamp:
            raise CustomException(
                msg="刷新令牌缺少过期时间",
                code=10401,
                status_code=401,
            )

        current_timestamp = int(
            time.time()
        )

        remaining_refresh_ttl = (
            int(refresh_exp_timestamp)
            - current_timestamp
        )

        if remaining_refresh_ttl <= 0:
            raise CustomException(
                msg="刷新令牌已过期，请重新登录",
                code=10401,
                status_code=401,
            )

        # ============================================================
        # 8. 新 Access Token
        # ============================================================

        now = now_beijing()

        session_info_json = json.dumps(
            session_info,
            ensure_ascii=False,
        )

        new_access_token = create_access_token(
            payload=JWTPayloadSchema(
                sub=session_info_json,
                is_refresh=False,
                exp=now
                + timedelta(
                    seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS
                ),
            )
        )

        # ============================================================
        # 9. 新 Refresh Token
        #
        # 重点：
        # exp 使用旧 Refresh Token 的最终 exp。
        #
        # 所以不会因为 refresh 而延长生命周期。
        # ============================================================

        new_refresh_token = create_access_token(
            payload=JWTPayloadSchema(
                sub=session_info_json,
                is_refresh=True,
                exp=datetime.fromtimestamp(refresh_exp_timestamp, tz=BEIJING_TIMEZONE),
            )
        )

        # ============================================================
        # 10. 保存新的 Access Token
        # ============================================================

        access_redis_key = (
            f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:"
            f"{session_id}"
        )

        await RedisCURD(redis).set(
            key=access_redis_key,
            value=new_access_token,
            expire=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        )

        # ============================================================
        # 11. 保存新的 Refresh Token
        #
        # 使用剩余 TTL。
        # ============================================================

        await RedisCURD(redis).set(
            key=refresh_redis_key,
            value=new_refresh_token,
            expire=remaining_refresh_ttl,
        )

        # ============================================================
        # 12. 请求上下文
        # ============================================================

        request.scope["session_id"] = (
            session_id
        )

        request.scope["user_id"] = (
            user.id
        )

        request.scope["user_username"] = (
            user.username
        )

        log.info(
            f"刷新Token成功: "
            f"user_id={user.id}, "
            f"session_id={session_id}, "
            f"remaining_refresh_ttl={remaining_refresh_ttl}s"
        )

        return JWTOutSchema(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type=settings.TOKEN_TYPE,
            expires_in=(
                settings.ACCESS_TOKEN_EXPIRE_SECONDS
            ),
        )

    # ==================================================================
    # Logout
    # ==================================================================

    @classmethod
    async def logout_service(
        cls,
        redis: Redis,
        token: LogoutPayloadSchema,
    ) -> bool:
        """退出登录。"""

        payload = decode_access_token(
            token=token.token
        )

        if payload.is_refresh:
            raise CustomException(
                msg="退出登录必须使用访问令牌",
                code=10401,
                status_code=401,
            )

        try:
            if isinstance(
                payload.sub,
                dict,
            ):
                session_info = payload.sub
            else:
                session_info = json.loads(
                    payload.sub
                )

        except (
            TypeError,
            json.JSONDecodeError,
        ):
            raise CustomException(
                msg="非法凭证",
                code=10401,
                status_code=401,
            )

        session_id = session_info.get(
            "session_id"
        )

        if not session_id:
            raise CustomException(
                msg="非法凭证，无法获取会话编号",
                code=10401,
                status_code=401,
            )

        # ============================================================
        # 删除 Access Token
        # ============================================================

        await RedisCURD(redis).delete(
            f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:"
            f"{session_id}"
        )

        # ============================================================
        # 删除 Refresh Token
        # ============================================================

        await RedisCURD(redis).delete(
            f"{RedisInitKeyConfig.REFRESH_TOKEN.key}:"
            f"{session_id}"
        )

        log.info(
            f"用户退出登录成功, "
            f"session_id={session_id}"
        )

        return True


class CaptchaService:
    """验证码服务。"""

    @classmethod
    async def get_captcha_service(
        cls,
        redis: Redis,
    ) -> dict[str, CaptchaKey | CaptchaBase64]:
        """获取验证码。"""

        if not settings.CAPTCHA_ENABLE:
            raise CustomException(
                msg="未开启验证码服务"
            )

        captcha_base64, captcha_value = (
            CaptchaUtil.captcha_arithmetic()
        )

        captcha_key = (
            get_random_character()
        )

        redis_key = (
            f"{RedisInitKeyConfig.CAPTCHA_CODES.key}:"
            f"{captcha_key}"
        )

        await RedisCURD(redis).set(
            key=redis_key,
            value=captcha_value,
            expire=settings.CAPTCHA_EXPIRE_SECONDS,
        )

        return CaptchaOutSchema(
            enable=settings.CAPTCHA_ENABLE,
            key=CaptchaKey(
                captcha_key
            ),
            img_base=CaptchaBase64(
                f"data:image/png;base64,{captcha_base64}"
            ),
        ).model_dump()

    @classmethod
    async def check_captcha_service(
        cls,
        redis: Redis,
        key: str,
        captcha: str,
    ) -> bool:
        """校验验证码。"""

        if not captcha:
            raise CustomException(
                msg="验证码不能为空"
            )

        redis_key = (
            f"{RedisInitKeyConfig.CAPTCHA_CODES.key}:"
            f"{key}"
        )

        captcha_value = (
            await RedisCURD(redis).get(
                redis_key
            )
        )

        if not captcha_value:
            raise CustomException(
                msg="验证码已过期"
            )

        if isinstance(
            captcha_value,
            bytes,
        ):
            captcha_value = (
                captcha_value.decode(
                    "utf-8"
                )
            )

        if captcha.lower() != str(
            captcha_value
        ).lower():
            raise CustomException(
                msg="验证码错误"
            )

        # 验证成功后立即删除。
        await RedisCURD(redis).delete(
            redis_key
        )

        return True


class AutoLoginService:
    """免登录服务。"""

    AUTO_LOGIN_PREFIX = (
        "fastapiadmin:auto_login:"
    )

    TOKEN_EXPIRE = 300

    @classmethod
    async def get_auto_login_users_service(
        cls,
        db: AsyncSession,
    ) -> list[AutoLoginUserSchema]:
        """获取可以免登录的用户列表。"""

        stmt = (
            select(UserModel)
            .where(
                UserModel.status == "0"
            )
            .order_by(
                UserModel.id
            )
        )

        result = await db.execute(stmt)

        users = result.scalars().all()

        return [
            AutoLoginUserSchema(
                id=user.id,
                username=user.username,
                name=user.name,
                avatar=user.avatar,
            )
            for user in users
        ]

    @classmethod
    async def create_auto_login_token_service(
        cls,
        redis: Redis,
        db: AsyncSession,
        user_id: int,
    ) -> AutoLoginTokenSchema:
        """创建一次性免登录 Token。"""

        stmt = select(UserModel).where(
            UserModel.id == user_id
        )

        result = await db.execute(stmt)

        user = result.scalar_one_or_none()

        if not user:
            raise CustomException(
                msg="用户不存在"
            )

        if user.status == "1":
            raise CustomException(
                msg="用户已被停用"
            )

        token = str(
            uuid.uuid4()
        )

        token_key = (
            f"{cls.AUTO_LOGIN_PREFIX}"
            f"{token}"
        )

        token_data = {
            "user_id": user.id,
            "username": user.username,
            "created_at": now_beijing().isoformat(),
        }

        await RedisCURD(redis).set(
            key=token_key,
            value=json.dumps(
                token_data,
                ensure_ascii=False,
            ),
            expire=cls.TOKEN_EXPIRE,
        )

        return AutoLoginTokenSchema(
            token=token,
            user=AutoLoginUserSchema(
                id=user.id,
                username=user.username,
                name=user.name,
                avatar=user.avatar,
            ),
        )

    @classmethod
    async def auto_login_service(
        cls,
        request: Request,
        redis: Redis,
        db: AsyncSession,
        token: str,
    ) -> JWTOutSchema:
        """使用一次性 Token 自动登录。"""

        token_key = (
            f"{cls.AUTO_LOGIN_PREFIX}"
            f"{token}"
        )

        token_data_str = (
            await RedisCURD(redis).get(
                token_key
            )
        )

        if not token_data_str:
            raise CustomException(
                msg="免登录Token已过期或无效"
            )

        if isinstance(
            token_data_str,
            bytes,
        ):
            token_data_str = (
                token_data_str.decode(
                    "utf-8"
                )
            )

        try:
            token_data = json.loads(
                token_data_str
            )
        except json.JSONDecodeError:
            raise CustomException(
                msg="免登录Token数据异常"
            )

        user_id = token_data.get(
            "user_id"
        )

        if not user_id:
            raise CustomException(
                msg="免登录Token数据异常"
            )

        stmt = select(UserModel).where(
            UserModel.id == user_id
        )

        result = await db.execute(stmt)

        user = result.scalar_one_or_none()

        if not user:
            raise CustomException(
                msg="用户不存在"
            )

        if user.status == "1":
            raise CustomException(
                msg="用户已被停用"
            )

        # ============================================================
        # 一次性使用
        # ============================================================

        await RedisCURD(redis).delete(
            token_key
        )

        # ============================================================
        # 创建正常登录 Token
        # ============================================================

        jwt_token = (
            await LoginService.create_token_service(
                request=request,
                redis=redis,
                user=user,
                login_type="PC端",
            )
        )

        log.info(
            f"用户{user.username}免登录成功"
        )

        return jwt_token
