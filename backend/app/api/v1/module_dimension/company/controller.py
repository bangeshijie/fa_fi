from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PageResultSchema
from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.base_schema import BatchSetAvailable
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import (
    CompanyCreateSchema,
    CompanyOptionSchema,
    CompanyOutSchema,
    CompanyQueryParam,
    CompanyUpdateSchema,
)
from .service import CompanyService


CompanyRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/company",
    tags=["公司主数据"],
)


@CompanyRouter.get(
    "/options",
    summary="查询公司选择项",
    response_model=ResponseSchema[list[CompanyOptionSchema]],
)
async def get_company_options_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:company:query"]))],
) -> JSONResponse:
    result = await CompanyService.get_company_options_service(auth=auth)
    return SuccessResponse(data=result, msg="查询公司选择项成功")


@CompanyRouter.get(
    "/list",
    summary="查询公司主数据",
    response_model=ResponseSchema[PageResultSchema],
)
async def get_company_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[CompanyQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:company:query"]))],
) -> JSONResponse:
    result = await CompanyService.get_company_page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询公司主数据成功")


@CompanyRouter.get(
    "/detail/{id}",
    summary="查询公司主数据详情",
    response_model=ResponseSchema[CompanyOutSchema],
)
async def get_company_detail_controller(
    id: Annotated[int, Path(description="公司ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:company:detail"]))],
) -> JSONResponse:
    result = await CompanyService.get_company_detail_service(auth=auth, id=id)
    return SuccessResponse(data=result, msg="查询公司详情成功")


@CompanyRouter.post(
    "/create",
    summary="创建公司主数据",
    response_model=ResponseSchema[CompanyOutSchema],
)
async def create_company_controller(
    data: CompanyCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:company:create"]))],
) -> JSONResponse:
    result = await CompanyService.create_company_service(auth=auth, data=data)
    return SuccessResponse(data=result, msg="创建公司成功")


@CompanyRouter.put(
    "/update/{id}",
    summary="修改公司主数据",
    response_model=ResponseSchema[CompanyOutSchema],
)
async def update_company_controller(
    data: CompanyUpdateSchema,
    id: Annotated[int, Path(description="公司ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:company:update"]))],
) -> JSONResponse:
    result = await CompanyService.update_company_service(auth=auth, id=id, data=data)
    return SuccessResponse(data=result, msg="修改公司成功")


@CompanyRouter.delete(
    "/delete",
    summary="删除公司主数据",
    response_model=ResponseSchema[None],
)
async def delete_company_controller(
    ids: Annotated[list[int], Body(description="公司ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:company:delete"]))],
) -> JSONResponse:
    await CompanyService.delete_company_service(auth=auth, ids=ids)
    return SuccessResponse(msg="删除公司成功")


@CompanyRouter.patch(
    "/available/setting",
    summary="批量修改公司状态",
    response_model=ResponseSchema[None],
)
async def set_company_available_controller(
    data: BatchSetAvailable,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:company:patch"]))],
) -> JSONResponse:
    await CompanyService.set_company_available_service(auth=auth, data=data)
    return SuccessResponse(msg="修改公司状态成功")


@CompanyRouter.post(
    "/export",
    summary="导出公司主数据",
    response_model=ResponseSchema[None],
)
async def export_company_controller(
    search: Annotated[CompanyQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_dimension:company:export"]))],
) -> StreamingResponse:
    company_list = await CompanyService.get_company_list_service(auth=auth, search=search)
    file_data = await CompanyService.export_company_list_service(company_list=company_list)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=company.xlsx"},
    )
