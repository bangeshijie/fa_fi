# main.py

import asyncio
from contextlib import asynccontextmanager

from app.api.v1.module_system.dict.service import DictDataService
from app.api.v1.module_system.params.service import ParamsService
from app.config.setting import settings
from app.core.database import redis_connect
from app.core.exceptions import handle_exception
from app.core.logger import log
from app.scripts.initialize import InitializeData
from app.task.operation_log_worker import operation_log_worker
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    log.info("🚀 应用正在启动...")

    log_worker_task = None

    try:
        # 初始化数据库
        await InitializeData().init_db()

        log.info(f"✅ {settings.DATABASE_TYPE} 数据库初始化完成")

        # 初始化Redis
        await redis_connect(app, status=True)

        await ParamsService().init_config_service(redis=app.state.redis)

        log.info("✅ Redis系统配置初始化完成")

        await DictDataService().init_dict_service(redis=app.state.redis)

        log.info("✅ Redis数据字典初始化完成")

        # 启动操作日志消费者
        log_worker_task = asyncio.create_task(operation_log_worker(app.state.redis))

        log.info("✅ 操作日志后台任务创建完成")

        yield

    except Exception as e:
        log.error(f"❌ 应用启动失败: {e}")

        raise RuntimeError(f"应用启动失败: {e}") from e

    finally:
        # 停止日志消费者
        if log_worker_task:
            log_worker_task.cancel()

            try:
                await log_worker_task

            except asyncio.CancelledError:
                pass

        log.info("🛑 应用正在关闭!!!")

        await redis_connect(app, status=False)

        log.info("🛑 应用已关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url="/api/openapi.json",
    responses={
        200: {"description": "成功"},
        400: {"description": "请求参数错误"},
        401: {"description": "未认证"},
        403: {"description": "未授权"},
        404: {"description": "资源不存在"},
        422: {"description": "请求参数验证错误"},
        500: {"description": "服务器内部错误"},
    },
)

# 注册全局异常处理器
handle_exception(app)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,  # 从配置文件读取
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
    expose_headers=["Content-Disposition"],
    max_age=3600,  # 预检请求缓存时间
)


# 注册路由


def register_routers(app: FastAPI) -> None:
    """注册路由"""

    from app.api.v1.module_common import common_router
    from app.api.v1.module_budget import budget_router
    from app.api.v1.module_dimension import dimension_router
    from app.api.v1.module_financial import financial_router
    from app.api.v1.module_monitor import monitor_router
    from app.api.v1.module_system import system_router

    api_prefix = "/api/v1"
    # 业务路由（暂时不带速率限制）

    app.include_router(common_router, prefix=api_prefix)
    app.include_router(dimension_router, prefix=api_prefix)
    app.include_router(financial_router, prefix=api_prefix)
    app.include_router(budget_router, prefix=api_prefix)
    app.include_router(system_router, prefix=api_prefix)
    app.include_router(monitor_router, prefix=api_prefix)


register_routers(app)


def register_files(app: FastAPI) -> None:
    """
    注册静态资源挂载和文件相关配置。

    参数:
    - app (FastAPI): FastAPI 应用实例。

    返回:
    - None
    """
    # 挂载静态文件目录
    if settings.STATIC_ENABLE:
        # 确保静态资源根目录存在
        settings.STATIC_ROOT.mkdir(parents=True, exist_ok=True)
        app.mount(
            path=settings.STATIC_URL,
            app=StaticFiles(directory=settings.STATIC_ROOT),
            name=settings.STATIC_DIR,
        )


register_files(app)
