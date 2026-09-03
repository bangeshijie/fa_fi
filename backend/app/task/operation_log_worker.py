
import json
import asyncio

from redis.asyncio import Redis

from app.core.database import async_db_session
from app.core.logger import log

from app.core.redis_crud import RedisCURD

from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.log.schema import OperationLogCreateSchema
from app.api.v1.module_system.log.service import OperationLogService
from app.utils.ip_local_util import IpLocalUtil

QUEUE_NAME = "operation_log_queue"

#======================================================
# 目前是redis获取后再截断,redis压力可能比较大,后面再改!!!!!!
# ======================================================
def limit_json_data(value, max_items: int = 100):
    """限制日志JSON数量，避免日志过大"""

    if not value:
        return value

    try:
        # 字符串JSON转对象
        if isinstance(value, str):
            obj = json.loads(value)
        else:
            obj = value

        # 截断逻辑...
        if isinstance(obj, list):
            if len(obj) > max_items:
                obj = obj[:max_items]
        elif isinstance(obj, dict):
            for key, val in obj.items():
                if isinstance(val, list):
                    if len(val) > max_items:
                        obj[key] = val[:max_items]

        return json.dumps(obj, ensure_ascii=False)

    except json.JSONDecodeError:
        # 不是合法JSON，按字符串截断
        if isinstance(value, str) and len(value) > 2000:
            return value[:2000]
        return value

    except TypeError:
        # 不可序列化对象，转为字符串
        str_value = str(value)
        return str_value[:2000] if len(str_value) > 2000 else str_value

async def operation_log_worker(
    redis: Redis
):

    log.info("✅ 操作日志消费者启动")


    redis_crud = RedisCURD(redis)


    while True:

        try:

            data = await redis_crud.dequeue(
                QUEUE_NAME,
                timeout=5
            )


            if not data:
                continue

            # ==========================
            # IP归属地查询
            # ==========================
            request_ip = data.get(
                "request_ip"
            )

            if request_ip and not data.get("login_location"):

                try:

                    data["login_location"] = (
                        await IpLocalUtil.resolve_location_for_log(
                            request_ip
                        )
                    )

                except Exception as e:

                    log.warning(
                        f"IP归属地解析失败:{e}"
                    )

                    data["login_location"] = None

            # ==========================
            # 保存日志
            # ==========================
            data["request_payload"] = limit_json_data(
                data.get("request_payload")
            )

            data["response_json"] = limit_json_data(
                data.get("response_json")
            )


            # 后台任务，没有当前登录用户
            async with async_db_session() as session:

                async with session.begin():

                    auth = AuthSchema(
                        db=session,
                        user=None,
                        check_data_scope=False
                    )


                    await OperationLogService.create_log_service(
                        data=OperationLogCreateSchema(
                            **data
                        ),
                        auth=auth
                    )


        except asyncio.CancelledError:

            log.info( "🛑 操作日志消费者关闭")

            break


        except Exception as e:

            log.exception(f"操作日志消费异常:{e}")

            await asyncio.sleep(5)
