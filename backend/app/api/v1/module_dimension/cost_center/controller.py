from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from redis.asyncio.client import Redis

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PageResultSchema
from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.base_schema import BatchSetAvailable
from app.core.dependencies import AuthPermission, redis_getter
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import (
    CostCenterCreateSchema,
    CostCenterImportResultSchema,
    CostCenterOptionSchema,
    CostCenterOutSchema,
    CostCenterQueryParam,
    CostCenterUpdateSchema,
    DepartmentOptionSchema,
)
from .service import CostCenterService


CostCenterRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/cost-center",
    tags=["成本中心主数据"],
)


@CostCenterRouter.get(
    "/options",
    summary="查询成本中心选择项",
    response_model=ResponseSchema[list[CostCenterOptionSchema]],
)
async def get_options_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:query"]))],
) -> JSONResponse:
    result = await CostCenterService.get_options_service(auth=auth)
    return SuccessResponse(data=result, msg="查询成本中心选择项成功")


@CostCenterRouter.get(
    "/department-options",
    summary="查询成本中心所属组织选择项",
    response_model=ResponseSchema[list[DepartmentOptionSchema]],
)
async def get_department_options_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:query"]))],
) -> JSONResponse:
    result = await CostCenterService.get_department_options_service(auth=auth)
    return SuccessResponse(data=result, msg="查询所属组织选择项成功")


@CostCenterRouter.post(
    "/import/template",
    summary="获取成本中心导入模板",
    response_model=ResponseSchema[None],
)
async def get_import_template_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:download"]))],
    redis: Annotated[Redis, Depends(redis_getter)],
) -> StreamingResponse:
    file_data = await CostCenterService.get_import_template_service(auth=auth, redis=redis)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=cost-center-template.xlsx",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@CostCenterRouter.post(
    "/import/data",
    summary="批量导入成本中心",
    response_model=ResponseSchema[CostCenterImportResultSchema],
)
async def import_controller(
    file: UploadFile,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:import"]))],
) -> JSONResponse:
    result = await CostCenterService.batch_import_service(auth=auth, file=file)
    message = (
        "成本中心导入完成"
        if result["failed_count"] == 0
        else "成本中心导入完成，但部分数据未成功处理，请查看失败明细"
    )
    return SuccessResponse(data=result, msg=message)


@CostCenterRouter.get(
    "/list",
    summary="查询成本中心主数据",
    response_model=ResponseSchema[PageResultSchema],
)
async def get_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[CostCenterQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:query"]))],
) -> JSONResponse:
    result = await CostCenterService.get_page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询成本中心主数据成功")


@CostCenterRouter.get(
    "/detail/{id}",
    summary="查询成本中心详情",
    response_model=ResponseSchema[CostCenterOutSchema],
)
async def get_detail_controller(
    id: Annotated[int, Path(description="成本中心ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:detail"]))],
) -> JSONResponse:
    result = await CostCenterService.get_detail_service(auth=auth, id=id)
    return SuccessResponse(data=result, msg="查询成本中心详情成功")


@CostCenterRouter.post(
    "/create",
    summary="创建成本中心",
    response_model=ResponseSchema[CostCenterOutSchema],
)
async def create_controller(
    data: CostCenterCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:create"]))],
) -> JSONResponse:
    result = await CostCenterService.create_service(auth=auth, data=data)
    return SuccessResponse(data=result, msg="创建成本中心成功")


@CostCenterRouter.put(
    "/update/{id}",
    summary="修改成本中心",
    response_model=ResponseSchema[CostCenterOutSchema],
)
async def update_controller(
    data: CostCenterUpdateSchema,
    id: Annotated[int, Path(description="成本中心ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:update"]))],
) -> JSONResponse:
    result = await CostCenterService.update_service(auth=auth, id=id, data=data)
    return SuccessResponse(data=result, msg="修改成本中心成功")


@CostCenterRouter.delete(
    "/delete",
    summary="删除成本中心",
    response_model=ResponseSchema[None],
)
async def delete_controller(
    ids: Annotated[list[int], Body(description="成本中心ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:delete"]))],
) -> JSONResponse:
    await CostCenterService.delete_service(auth=auth, ids=ids)
    return SuccessResponse(msg="删除成本中心成功")


@CostCenterRouter.patch(
    "/available/setting",
    summary="批量修改成本中心状态",
    response_model=ResponseSchema[None],
)
async def set_available_controller(
    data: BatchSetAvailable,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:patch"]))],
) -> JSONResponse:
    await CostCenterService.set_available_service(auth=auth, data=data)
    return SuccessResponse(msg="修改成本中心状态成功")


@CostCenterRouter.post(
    "/export",
    summary="导出成本中心主数据",
    response_model=ResponseSchema[None],
)
async def export_controller(
    search: Annotated[CostCenterQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:cost_center:export"]))],
) -> StreamingResponse:
    items = await CostCenterService.get_list_service(auth=auth, search=search)
    file_data = await CostCenterService.export_service(items=items)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=cost-center.xlsx"},
    )
