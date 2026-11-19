from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.dept.schema import DeptOutSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute

from .schema import ExpenseAnalysisQuerySchema, ExpenseAnalysisResponseSchema
from .service import ExpenseAnalysisService


ExpenseAnalysisRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/expense-analysis",
    tags=["费用分析"],
)


@ExpenseAnalysisRouter.get(
    "/departments",
    summary="查询费用分析部门选项",
    response_model=ResponseSchema[list[DeptOutSchema]],
)
async def get_department_options_controller(
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_financial:expense_analysis:query"]))
    ],
) -> JSONResponse:
    result = await ExpenseAnalysisService.get_department_options_service(auth=auth)
    return SuccessResponse(data=result, msg="查询费用分析部门选项成功")


@ExpenseAnalysisRouter.post(
    "/query",
    summary="查询费用分析",
    response_model=ResponseSchema[ExpenseAnalysisResponseSchema],
)
async def query_controller(
    query: ExpenseAnalysisQuerySchema,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_financial:expense_analysis:query"]))
    ],
) -> JSONResponse:
    result = await ExpenseAnalysisService.query_service(auth=auth, query=query)
    return SuccessResponse(data=result, msg="查询费用分析成功")
