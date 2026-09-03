import ipaddress
import json
import time
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute
from user_agents import parse


from app.config.setting import settings

from app.core.redis_crud import RedisCURD
from app.utils.ip_local_util import IpLocalUtil


_SENSITIVE_LOG_KEYS = frozenset(
    {
        "token",
        "access_token",
        "refresh_token",
        "client_secret",
        "secret",
    }
)
_REDACTED_VALUE = "******"


def _is_sensitive_log_key(key: Any) -> bool:
    """判断字段是否可能包含密码或其他认证凭据。"""
    normalized_key = str(key).strip().lower().replace("-", "_")
    return (
        normalized_key in _SENSITIVE_LOG_KEYS
        or "password" in normalized_key
        or "passwd" in normalized_key
        or normalized_key in {"pwd", "old_pwd", "new_pwd", "confirm_pwd"}
    )


def _redact_log_value(value: Any) -> Any:
    """递归脱敏 JSON 中的密码、Token 等敏感字段。"""
    if isinstance(value, dict):
        return {
            key: (
                _REDACTED_VALUE
                if _is_sensitive_log_key(key)
                else _redact_log_value(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_log_value(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_log_value(item) for item in value]
    return value


def _redact_serialized_json(value: str) -> str:
    """脱敏 JSON 字符串；非 JSON 内容原样返回。"""
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value
    return json.dumps(_redact_log_value(parsed), ensure_ascii=False)


def _get_client_ip(request: Request) -> str | None:
    """从代理头或连接信息中取得经过校验的客户端 IP。"""
    candidates: list[str] = []

    # 反向代理通常将最左侧地址作为原始客户端地址。
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    candidates.extend(item.strip() for item in forwarded_for.split(",") if item.strip())

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        candidates.append(real_ip.strip())

    if request.client:
        candidates.append(request.client.host)

    for candidate in candidates:
        # 兼容少数代理传来的 [IPv6] 或 [IPv6]:port 格式。
        normalized = candidate.strip()
        if normalized.startswith("[") and "]" in normalized:
            normalized = normalized[1 : normalized.index("]")]
        try:
            return str(ipaddress.ip_address(normalized))
        except ValueError:
            continue
    return None
"""
在 FastAPI 中，route_class 参数用于自定义路由的行为。
通过设置 route_class，你可以定义一个自定义的路由类，从而在每个路由处理之前或之后执行特定的操作。
这对于日志记录、权限验证、性能监控等场景非常有用。
"""


class OperationLogRoute(APIRoute):
    """操作日志路由装饰器"""

    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        """
        自定义路由处理程序,在每个路由处理之前或之后执行特定的操作。

        参数:
        - request (Request): FastAPI请求对象。

        返回:
        - Response: FastAPI响应对象。
        """
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            """
            自定义路由处理程序,在每个路由处理之前或之后执行特定的操作。

            参数:
            - request (Request): FastAPI请求对象。
            描述:
            - 该方法在每个路由处理之前被调用,用于记录操作日志。
            返回:
            - Response: FastAPI响应对象。
            """
            start_time = time.time()
            # 请求前的处理
            response: Response = await original_route_handler(request)

            # 请求后的处理
            if not settings.OPERATION_LOG_RECORD:
                return response
            if request.method not in settings.OPERATION_RECORD_METHOD:
                return response
            route: APIRoute = request.scope.get("route", None)
            if route.name in settings.IGNORE_OPERATION_FUNCTION:
                return response

            user_agent = parse(request.headers.get("user-agent"))
            
            req_content_type = request.headers.get("Content-Type", "")

            if req_content_type and (
                req_content_type.startswith((
                    "multipart/form-data",
                    "application/x-www-form-urlencoded",
                ))
            ):
                form_data = await request.form()
                oper_param = "\n".join(
                    f"{key}: "
                    f"{_REDACTED_VALUE if _is_sensitive_log_key(key) else value}"
                    for key, value in form_data.multi_items()
                )
                payload = oper_param
            else:
                payload = await request.body()
                path_params = request.path_params
                oper_param = {}

                # 处理请求体数据
                if payload:
                    try:
                        oper_param["body"] = _redact_log_value(
                            json.loads(payload.decode())
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        oper_param["body"] = payload.decode("utf-8", errors="ignore")

                # 处理路径参数
                if path_params:
                    oper_param["path_params"] = dict(path_params)

                payload = json.dumps(oper_param, ensure_ascii=False)

            # 日志表请求参数字段长度最大为 2000。
            if len(payload) > 2000:
                payload = "请求参数过长"

            response_data = (
                response.body
                if "application/json" in response.headers.get("Content-Type", "")
                else b"{}"
            )
            response_json = (
                response_data.decode("utf-8", errors="ignore")
                if isinstance(response_data, (bytes, bytearray))
                else str(response_data)
            )
            response_json = _redact_serialized_json(response_json)[:2000]
            process_time = f"{(time.time() - start_time):.2f}s"

            # 获取当前用户ID,如果是登录接口则为空
            log_type = 1  # 1:登录日志 2:操作日志
            current_user_id = None

            # 优化：只在操作日志场景下获取current_user_id
            if "user_id" in request.scope:
                current_user_id = request.scope.get("user_id")
                log_type = 2

            request_ip = _get_client_ip(request)

            # 登录服务通常已经解析过归属地；若没有（例如认证失败），登录路由
            # 在这里补解析。其他操作由 operation_log_worker 异步解析，避免拖慢请求。
            login_location = request.scope.get("login_location")
            if log_type == 1 and request_ip and not login_location:
                try:
                    login_location = await IpLocalUtil.resolve_location_for_log(
                        request_ip
                    )
                except Exception:
                    # 归属地服务不可用时不能影响原始业务响应。
                    login_location = None

            # 判断请求是否来自api文档
            referer = request.headers.get("referer")
            request_from_swagger = referer and referer.endswith("docs")
            request_from_redoc = referer and referer.endswith("redoc")

            if request_from_swagger or request_from_redoc:
                # 如果请求来自api文档，则不记录日志
                pass
            else:

                redis_crud = RedisCURD(
                    request.app.state.redis
                )

                await redis_crud.enqueue(
                    "operation_log_queue",
                    {
                        "type": log_type,
                        "request_path": request.url.path,
                        "request_method": request.method,
                        "request_payload": payload,
                        "request_ip": request_ip,
                        "login_location": login_location,
                        "request_os": user_agent.os.family,
                        "request_browser": user_agent.browser.family,
                        "response_code": response.status_code,
                        "response_json": response_json,
                        "process_time": process_time,
                        "description": route.summary,
                        "created_id": current_user_id,
                        "updated_id": current_user_id,
                    }
                )

            return response

        return custom_route_handler
