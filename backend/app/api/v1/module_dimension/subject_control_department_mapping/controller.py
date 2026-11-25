from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PageResultSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.base_schema import BatchSetAvailable
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute

from .schema import (
    SubjectControlDepartmentMappingCreateSchema,
    SubjectControlDepartmentMappingOptionsSchema,
    SubjectControlDepartmentMappingOutSchema,
    SubjectControlDepartmentMappingQueryParam,
    SubjectControlDepartmentMappingUpdateSchema,
)
from .service import SubjectControlDepartmentMappingService


SubjectControlDepartmentMappingRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/subject-control-department-mapping",
    tags=["科目主控部门映射"],
)


@SubjectControlDepartmentMappingRouter.get(
    "/options",
    summary="查询科目主控部门映射选项",
    response_model=ResponseSchema[SubjectControlDepartmentMappingOptionsSchema],
)
async def get_options_controller(
    auth: Annotated[
        AuthSchema,
        Depends(
            AuthPermission(["module_dimension:subject_control_department_mapping:query"])
        ),
    ],
) -> JSONResponse:
    result = await SubjectControlDepartmentMappingService.get_options_service(auth=auth)
    return SuccessResponse(data=result, msg="查询科目主控部门映射选项成功")


@SubjectControlDepartmentMappingRouter.get(
    "/list",
    summary="查询科目主控部门映射",
    response_model=ResponseSchema[PageResultSchema],
)
async def get_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[SubjectControlDepartmentMappingQueryParam, Depends()],
    auth: Annotated[
        AuthSchema,
        Depends(
            AuthPermission(["module_dimension:subject_control_department_mapping:query"])
        ),
    ],
) -> JSONResponse:
    result = await SubjectControlDepartmentMappingService.get_page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询科目主控部门映射成功")


@SubjectControlDepartmentMappingRouter.get(
    "/detail/{id}",
    summary="查询科目主控部门映射详情",
    response_model=ResponseSchema[SubjectControlDepartmentMappingOutSchema],
)
async def get_detail_controller(
    id: Annotated[int, Path(description="科目主控部门映射ID")],
    auth: Annotated[
        AuthSchema,
        Depends(
            AuthPermission(["module_dimension:subject_control_department_mapping:detail"])
        ),
    ],
) -> JSONResponse:
    result = await SubjectControlDepartmentMappingService.get_detail_service(auth=auth, id=id)
    return SuccessResponse(data=result, msg="查询科目主控部门映射详情成功")


@SubjectControlDepartmentMappingRouter.post(
    "/create",
    summary="创建科目主控部门映射",
    response_model=ResponseSchema[SubjectControlDepartmentMappingOutSchema],
)
async def create_controller(
    data: SubjectControlDepartmentMappingCreateSchema,
    auth: Annotated[
        AuthSchema,
        Depends(
            AuthPermission(["module_dimension:subject_control_department_mapping:create"])
        ),
    ],
) -> JSONResponse:
    result = await SubjectControlDepartmentMappingService.create_service(auth=auth, data=data)
    return SuccessResponse(data=result, msg="创建科目主控部门映射成功")


@SubjectControlDepartmentMappingRouter.put(
    "/update/{id}",
    summary="修改科目主控部门映射",
    response_model=ResponseSchema[SubjectControlDepartmentMappingOutSchema],
)
async def update_controller(
    data: SubjectControlDepartmentMappingUpdateSchema,
    id: Annotated[int, Path(description="科目主控部门映射ID")],
    auth: Annotated[
        AuthSchema,
        Depends(
            AuthPermission(["module_dimension:subject_control_department_mapping:update"])
        ),
    ],
) -> JSONResponse:
    result = await SubjectControlDepartmentMappingService.update_service(
        auth=auth, id=id, data=data
    )
    return SuccessResponse(data=result, msg="修改科目主控部门映射成功")


@SubjectControlDepartmentMappingRouter.delete(
    "/delete",
    summary="删除科目主控部门映射",
    response_model=ResponseSchema[None],
)
async def delete_controller(
    ids: Annotated[list[int], Body(description="ID列表")],
    auth: Annotated[
        AuthSchema,
        Depends(
            AuthPermission(["module_dimension:subject_control_department_mapping:delete"])
        ),
    ],
) -> JSONResponse:
    await SubjectControlDepartmentMappingService.delete_service(auth=auth, ids=ids)
    return SuccessResponse(msg="删除科目主控部门映射成功")


@SubjectControlDepartmentMappingRouter.patch(
    "/available/setting",
    summary="批量修改科目主控部门映射状态",
    response_model=ResponseSchema[None],
)
async def set_available_controller(
    data: BatchSetAvailable,
    auth: Annotated[
        AuthSchema,
        Depends(
            AuthPermission(["module_dimension:subject_control_department_mapping:patch"])
        ),
    ],
) -> JSONResponse:
    await SubjectControlDepartmentMappingService.set_available_service(auth=auth, data=data)
    return SuccessResponse(msg="修改科目主控部门映射状态成功")
