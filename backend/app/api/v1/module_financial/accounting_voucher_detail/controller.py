from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PageResultSchema
from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import (
    AccountingVoucherDetailCreateSchema,
    AccountingVoucherDetailImportResultSchema,
    AccountingVoucherDetailOutSchema,
    AccountingVoucherDetailPageSchema,
    AccountingVoucherDetailQueryParam,
    AccountingVoucherDetailUpdateSchema,
)
from .service import AccountingVoucherDetailService


AccountingVoucherDetailRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/accounting-voucher-detail",
    tags=["会计凭证明细"],
)


@AccountingVoucherDetailRouter.post(
    "/import/template",
    summary="获取会计凭证明细导入模板",
    response_model=ResponseSchema[None],
)
async def get_import_template_controller(
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_financial:accounting_voucher_detail:download"])),
    ],
) -> StreamingResponse:
    file_data = await AccountingVoucherDetailService.get_import_template_service(auth=auth)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=accounting-voucher-detail-template.xlsx",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@AccountingVoucherDetailRouter.post(
    "/import/data",
    summary="批量导入会计凭证明细",
    response_model=ResponseSchema[AccountingVoucherDetailImportResultSchema],
)
async def import_controller(
    file: UploadFile,
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_financial:accounting_voucher_detail:import"])),
    ],
) -> JSONResponse:
    result = await AccountingVoucherDetailService.batch_import_service(auth=auth, file=file)
    message = (
        "会计凭证明细导入完成"
        if result["failed_count"] == 0
        else "会计凭证明细导入完成，但部分数据未成功处理，请查看失败明细"
    )
    return SuccessResponse(data=result, msg=message)


@AccountingVoucherDetailRouter.get(
    "/list",
    summary="查询会计凭证明细",
    response_model=ResponseSchema[AccountingVoucherDetailPageSchema],
)
async def get_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[AccountingVoucherDetailQueryParam, Depends()],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_financial:accounting_voucher_detail:query"]))
    ],
) -> JSONResponse:
    result = await AccountingVoucherDetailService.get_page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询会计凭证明细成功")


@AccountingVoucherDetailRouter.get(
    "/detail/{id}",
    summary="查询会计凭证明细详情",
    response_model=ResponseSchema[AccountingVoucherDetailOutSchema],
)
async def get_detail_controller(
    id: Annotated[int, Path(description="会计凭证明细ID")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_financial:accounting_voucher_detail:detail"]))
    ],
) -> JSONResponse:
    result = await AccountingVoucherDetailService.get_detail_service(auth=auth, id=id)
    return SuccessResponse(data=result, msg="查询会计凭证明细详情成功")


@AccountingVoucherDetailRouter.post(
    "/create",
    summary="创建会计凭证明细",
    response_model=ResponseSchema[AccountingVoucherDetailOutSchema],
)
async def create_controller(
    data: AccountingVoucherDetailCreateSchema,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_financial:accounting_voucher_detail:create"]))
    ],
) -> JSONResponse:
    result = await AccountingVoucherDetailService.create_service(auth=auth, data=data)
    return SuccessResponse(data=result, msg="创建会计凭证明细成功")


@AccountingVoucherDetailRouter.put(
    "/update/{id}",
    summary="修改会计凭证明细",
    response_model=ResponseSchema[AccountingVoucherDetailOutSchema],
)
async def update_controller(
    data: AccountingVoucherDetailUpdateSchema,
    id: Annotated[int, Path(description="会计凭证明细ID")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_financial:accounting_voucher_detail:update"]))
    ],
) -> JSONResponse:
    result = await AccountingVoucherDetailService.update_service(auth=auth, id=id, data=data)
    return SuccessResponse(data=result, msg="修改会计凭证明细成功")


@AccountingVoucherDetailRouter.delete(
    "/delete",
    summary="删除会计凭证明细",
    response_model=ResponseSchema[None],
)
async def delete_controller(
    ids: Annotated[list[int], Body(description="会计凭证明细ID列表")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_financial:accounting_voucher_detail:delete"]))
    ],
) -> JSONResponse:
    await AccountingVoucherDetailService.delete_service(auth=auth, ids=ids)
    return SuccessResponse(msg="删除会计凭证明细成功")


@AccountingVoucherDetailRouter.post(
    "/export",
    summary="导出会计凭证明细",
    response_model=ResponseSchema[None],
)
async def export_controller(
    search: Annotated[AccountingVoucherDetailQueryParam, Depends()],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_financial:accounting_voucher_detail:export"]))
    ],
) -> StreamingResponse:
    items = await AccountingVoucherDetailService.get_list_service(auth=auth, search=search)
    file_data = await AccountingVoucherDetailService.export_service(items=items)
    return StreamResponse(
        data=bytes2file_response(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=accounting-voucher-detail.xlsx"},
    )
