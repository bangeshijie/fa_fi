from datetime import datetime
from typing import Annotated

import jwt
from fastapi import Form
from fastapi.security import OAuth2PasswordBearer

from app.config.setting import settings
from app.core.exceptions import CustomException

from app.api.v1.module_system.auth.schema import JWTPayloadSchema


# ============================================================================
# OAuth2
# ============================================================================

OAuth2Schema = OAuth2PasswordBearer(
    tokenUrl="/api/v1/system/auth/login",
    auto_error=False,
)


# ============================================================================
# OAuth2 登录表单
# ============================================================================

class CustomOAuth2PasswordRequestForm:
    """
    自定义 OAuth2 登录表单。

    在标准 OAuth2PasswordRequestForm 的基础上，
    保留项目自己的登录字段：

    username
    password
    captcha_key
    captcha
    login_type

    注意：
    login_type 默认使用「PC端」。

    这样做的原因是：
    Swagger UI 的 OAuth2 Authorize 只会自动提交
    username / password 等标准 OAuth2 字段，
    不会主动提交项目自定义的 login_type。

    因此 Swagger 登录时：
        login_type = "PC端"

    普通前端登录时：
        可以主动传入自己的 login_type。
    """

    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
        captcha_key: str | None = Form(None),
        captcha: str | None = Form(None),
        login_type: str = Form("PC端"),
    ):
        self.username = username
        self.password = password
        self.captcha_key = captcha_key
        self.captcha = captcha
        self.login_type = login_type


# ============================================================================
# JWT
# ============================================================================

def create_access_token(
    payload: JWTPayloadSchema,
) -> str:
    """
    创建 JWT。

    注意：
    exp 由调用方传入。

    PyJWT 在 decode 时会自动验证 exp。
    """

    payload_dict = payload.model_dump(
        exclude_none=False
    )

    return jwt.encode(
        payload=payload_dict,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> JWTPayloadSchema:
    """
    解析并验证 JWT。

    验证：

    1. Token 是否存在
    2. JWT 签名是否正确
    3. exp 是否过期
    4. sub 是否存在
    5. JWT payload 是否符合 JWTPayloadSchema

    注意：

    这里负责的是 JWT 本身的验证。

    Redis 中 Access Token 是否仍然有效，
    由 dependencies.py 中的：

        _verify_redis_access_token()

    负责。

    因此当前项目实际上是：

        JWT
          +
        Redis Session

    双重认证。
    """

    # ========================================================================
    # 1. Token 是否存在
    # ========================================================================

    if not token:
        raise CustomException(
            msg="认证不存在，请重新登录",
            code=10401,
            status_code=401,
        )

    token = token.strip()

    if not token:
        raise CustomException(
            msg="认证不存在，请重新登录",
            code=10401,
            status_code=401,
        )

    # ========================================================================
    # 2. 防止调用方直接传：
    #
    #    Bearer eyJ...
    #
    # 虽然 OAuth2Schema 正常情况下只会返回 token，
    # 这里仍然兼容手动调用。
    # ========================================================================

    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    if not token:
        raise CustomException(
            msg="认证不存在，请重新登录",
            code=10401,
            status_code=401,
        )

    # ========================================================================
    # 3. JWT Decode
    # ========================================================================

    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "require": [
                    "sub",
                    "exp",
                ]
            },
        )

        # ====================================================================
        # 4. 检查 sub
        # ====================================================================

        online_user_info = payload.get("sub")

        if not online_user_info:
            raise CustomException(
                msg="无效认证，请重新登录",
                code=10401,
                status_code=401,
            )

        # ====================================================================
        # 5. 转换为 Pydantic Schema
        # ====================================================================

        return JWTPayloadSchema(
            **payload
        )

    # ========================================================================
    # JWT 已过期
    # ========================================================================

    except jwt.ExpiredSignatureError:
        raise CustomException(
            msg="认证已过期",
            code=10401,
            status_code=401,
        )

    # ========================================================================
    # JWT 签名错误
    # ========================================================================

    except jwt.InvalidSignatureError:
        raise CustomException(
            msg="无效认证，请重新登录",
            code=10401,
            status_code=401,
        )

    # ========================================================================
    # JWT Decode 错误
    # ========================================================================

    except jwt.DecodeError:
        raise CustomException(
            msg="无效认证，请重新登录",
            code=10401,
            status_code=401,
        )

    # ========================================================================
    # 其他 JWT 错误
    # ========================================================================

    except jwt.InvalidTokenError:
        raise CustomException(
            msg="Token 已失效，请重新登录",
            code=10401,
            status_code=401,
        )

    # ========================================================================
    # 自定义异常直接向上抛
    # ========================================================================

    except CustomException:
        raise

    # ========================================================================
    # 其他未知异常
    # ========================================================================

    except Exception as exc:
        raise CustomException(
            msg="认证解析失败，请重新登录",
            code=10401,
            status_code=401,
        ) from exc