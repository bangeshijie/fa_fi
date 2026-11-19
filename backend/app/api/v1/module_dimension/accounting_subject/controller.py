from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PageResultSchema
from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.base_schema import BatchSetAvailable
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import (
    AccountingSubjectCreateSchema,
    AccountingSubjectCategoryOptionSchema,
    AccountingSubjectImportResultSchema,
    AccountingSubjectOutSchema,
    AccountingSubjectOptionSchema,
    AccountingSubjectQueryParam,
    AccountingSubjectUpdateSchema,
)
from .service import AccountingSubjectService


AccountingSubjectRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/accounting-subject",
    tags=["会计科目主数据"],
)


@AccountingSubjectRouter.get(
    "/options",
    summary="查询会计科目选择项",
    response_model=ResponseSchema[list[AccountingSubjectOptionSchema]],
)
async def get_options_controller(
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:query"]))
    ],
) -> JSONResponse:
    result = await AccountingSubjectService.get_options_service(auth=auth)
    return SuccessResponse(data=result, msg="查询会计科目选择项成功")


@AccountingSubjectRouter.get(
    "/category-options",
    summary="查询会计科目管理分类树",
    response_model=ResponseSchema[list[AccountingSubjectCategoryOptionSchema]],
)
async def get_category_options_controller(
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:query"]))
    ],
) -> JSONResponse:
    result = await AccountingSubjectService.get_category_options_service(auth=auth)
    return SuccessResponse(data=result, msg="查询管理分类树成功")


@AccountingSubjectRouter.post(
    "/import/template",
    summary="获取会计科目导入模板",
    response_model=ResponseSchema[None],
)
async def get_import_template_controller(
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_dimension:accounting_subject:download"])),
    ],
) -> StreamingResponse:
    file_data = await AccountingSubjectService.get_import_template_service(auth=auth)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=accounting-subject-template.xlsx",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@AccountingSubjectRouter.post(
    "/import/data",
    summary="批量导入会计科目",
    response_model=ResponseSchema[AccountingSubjectImportResultSchema],
)
async def import_controller(
    file: UploadFile,
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_dimension:accounting_subject:import"])),
    ],
) -> JSONResponse:
    result = await AccountingSubjectService.batch_import_service(auth=auth, file=file)
    message = (
        "会计科目导入完成"
        if result["failed_count"] == 0
        else "会计科目导入完成，但部分数据未成功处理，请查看失败明细"
    )
    return SuccessResponse(data=result, msg=message)


@AccountingSubjectRouter.get(
    "/list",
    summary="查询会计科目主数据",
    response_model=ResponseSchema[PageResultSchema],
)
async def get_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[AccountingSubjectQueryParam, Depends()],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:query"]))
    ],
) -> JSONResponse:
    result = await AccountingSubjectService.get_page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询会计科目主数据成功")


@AccountingSubjectRouter.get(
    "/detail/{id}",
    summary="查询会计科目详情",
    response_model=ResponseSchema[AccountingSubjectOutSchema],
)
async def get_detail_controller(
    id: Annotated[int, Path(description="会计科目ID")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:detail"]))
    ],
) -> JSONResponse:
    result = await AccountingSubjectService.get_detail_service(auth=auth, id=id)
    return SuccessResponse(data=result, msg="查询会计科目详情成功")


@AccountingSubjectRouter.post(
    "/create",
    summary="创建会计科目",
    response_model=ResponseSchema[AccountingSubjectOutSchema],
)
async def create_controller(
    data: AccountingSubjectCreateSchema,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:create"]))
    ],
) -> JSONResponse:
    result = await AccountingSubjectService.create_service(auth=auth, data=data)
    return SuccessResponse(data=result, msg="创建会计科目成功")


@AccountingSubjectRouter.put(
    "/update/{id}",
    summary="修改会计科目",
    response_model=ResponseSchema[AccountingSubjectOutSchema],
)
async def update_controller(
    data: AccountingSubjectUpdateSchema,
    id: Annotated[int, Path(description="会计科目ID")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:update"]))
    ],
) -> JSONResponse:
    result = await AccountingSubjectService.update_service(auth=auth, id=id, data=data)
    return SuccessResponse(data=result, msg="修改会计科目成功")


@AccountingSubjectRouter.delete(
    "/delete",
    summary="删除会计科目",
    response_model=ResponseSchema[None],
)
async def delete_controller(
    ids: Annotated[list[int], Body(description="会计科目ID列表")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:delete"]))
    ],
) -> JSONResponse:
    await AccountingSubjectService.delete_service(auth=auth, ids=ids)
    return SuccessResponse(msg="删除会计科目成功")


@AccountingSubjectRouter.patch(
    "/available/setting",
    summary="批量修改会计科目状态",
    response_model=ResponseSchema[None],
)
async def set_available_controller(
    data: BatchSetAvailable,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:patch"]))
    ],
) -> JSONResponse:
    await AccountingSubjectService.set_available_service(auth=auth, data=data)
    return SuccessResponse(msg="修改会计科目状态成功")


@AccountingSubjectRouter.post(
    "/export",
    summary="导出会计科目主数据",
    response_model=ResponseSchema[None],
)
async def export_controller(
    search: Annotated[AccountingSubjectQueryParam, Depends()],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_dimension:accounting_subject:export"]))
    ],
) -> StreamingResponse:
    items = await AccountingSubjectService.get_list_service(auth=auth, search=search)
    file_data = await AccountingSubjectService.export_service(items=items)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=accounting-subject.xlsx"},
    )
