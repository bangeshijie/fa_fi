from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.dept.schema import DeptOutSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute

from .schema import (
    ManagementFinanceVarianceQuerySchema,
    ManagementFinanceVarianceResponseSchema,
)
from .service import ManagementFinanceVarianceService


MANAGEMENT_FINANCE_VARIANCE_PERMISSION = "module_financial:management_finance_variance:query"

ManagementFinanceVarianceRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/management-finance-variance",
    tags=["管财差异分析"],
)


@ManagementFinanceVarianceRouter.get(
    "/departments",
    summary="查询管财差异分析部门选项",
    response_model=ResponseSchema[list[DeptOutSchema]],
)
async def get_department_options_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission([MANAGEMENT_FINANCE_VARIANCE_PERMISSION]))],
) -> JSONResponse:
    result = await ManagementFinanceVarianceService.get_department_options_service(auth=auth)
    return SuccessResponse(data=result, msg="查询管财差异分析部门选项成功")


@ManagementFinanceVarianceRouter.post(
    "/query",
    summary="查询管财差异分析",
    response_model=ResponseSchema[ManagementFinanceVarianceResponseSchema],
)
async def query_controller(
    query: ManagementFinanceVarianceQuerySchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission([MANAGEMENT_FINANCE_VARIANCE_PERMISSION]))],
) -> JSONResponse:
    result = await ManagementFinanceVarianceService.query_service(auth=auth, query=query)
    return SuccessResponse(data=result, msg="查询管财差异分析成功")
