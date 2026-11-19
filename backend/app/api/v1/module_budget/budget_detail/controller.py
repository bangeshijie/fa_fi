from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from redis.asyncio.client import Redis

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PageResultSchema
from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission, redis_getter
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import (
    BudgetDetailCreateSchema,
    BudgetDetailImportResultSchema,
    BudgetDetailOutSchema,
    BudgetDetailPageSchema,
    BudgetDetailQueryParam,
    BudgetDetailUpdateSchema,
)
from .service import BudgetDetailService


BudgetDetailRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/budget-detail",
    tags=["预算明细"],
)


@BudgetDetailRouter.post(
    "/import/template",
    summary="获取预算明细导入模板",
    response_model=ResponseSchema[None],
)
async def get_import_template_controller(
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_budget:budget_detail:download"])),
    ],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> StreamingResponse:
    file_data = await BudgetDetailService.get_import_template_service(auth=auth, redis=redis)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=budget-detail-template.xlsx",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@BudgetDetailRouter.post(
    "/import/data",
    summary="批量导入预算明细",
    response_model=ResponseSchema[BudgetDetailImportResultSchema],
)
async def import_controller(
    file: UploadFile,
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_budget:budget_detail:import"])),
    ],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    result = await BudgetDetailService.batch_import_service(auth=auth, file=file, redis=redis)
    message = (
        "预算明细导入完成"
        if result["failed_count"] == 0
        else "预算明细导入完成，但部分数据未成功处理，请查看失败明细"
    )
    return SuccessResponse(data=result, msg=message)


@BudgetDetailRouter.get(
    "/list",
    summary="查询预算明细",
    response_model=ResponseSchema[BudgetDetailPageSchema],
)
async def get_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[BudgetDetailQueryParam, Depends()],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_budget:budget_detail:query"]))
    ],
) -> JSONResponse:
    result = await BudgetDetailService.get_page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询预算明细成功")


@BudgetDetailRouter.get(
    "/detail/{id}",
    summary="查询预算明细详情",
    response_model=ResponseSchema[BudgetDetailOutSchema],
)
async def get_detail_controller(
    id: Annotated[int, Path(description="预算明细ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_budget:budget_detail:detail"]))],
) -> JSONResponse:
    result = await BudgetDetailService.get_detail_service(auth=auth, id=id)
    return SuccessResponse(data=result, msg="查询预算明细详情成功")


@BudgetDetailRouter.post(
    "/create",
    summary="创建预算明细",
    response_model=ResponseSchema[BudgetDetailOutSchema],
)
async def create_controller(
    data: BudgetDetailCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_budget:budget_detail:create"]))],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    result = await BudgetDetailService.create_service(auth=auth, data=data, redis=redis)
    return SuccessResponse(data=result, msg="创建预算明细成功")


@BudgetDetailRouter.put(
    "/update/{id}",
    summary="修改预算明细",
    response_model=ResponseSchema[BudgetDetailOutSchema],
)
async def update_controller(
    data: BudgetDetailUpdateSchema,
    id: Annotated[int, Path(description="预算明细ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_budget:budget_detail:update"]))],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> JSONResponse:
    result = await BudgetDetailService.update_service(auth=auth, id=id, data=data, redis=redis)
    return SuccessResponse(data=result, msg="修改预算明细成功")


@BudgetDetailRouter.delete(
    "/delete",
    summary="删除预算明细",
    response_model=ResponseSchema[None],
)
async def delete_controller(
    ids: Annotated[list[int], Body(description="预算明细ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_budget:budget_detail:delete"]))],
) -> JSONResponse:
    await BudgetDetailService.delete_service(auth=auth, ids=ids)
    return SuccessResponse(msg="删除预算明细成功")


@BudgetDetailRouter.post(
    "/export",
    summary="导出预算明细",
    response_model=ResponseSchema[None],
)
async def export_controller(
    search: Annotated[BudgetDetailQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_budget:budget_detail:export"]))],
) -> StreamingResponse:
    items = await BudgetDetailService.get_list_service(auth=auth, search=search)
    file_data = await BudgetDetailService.export_service(items=items)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=budget-detail.xlsx"},
    )
