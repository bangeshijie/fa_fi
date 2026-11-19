"""预算明细业务服务。"""

import io
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from fastapi import UploadFile, status as http_status
from redis.asyncio.client import Redis

from app.api.v1.module_dimension.accounting_subject.crud import AccountingSubjectCRUD
from app.api.v1.module_dimension.company.crud import CompanyCRUD
from app.api.v1.module_dimension.cost_center.crud import CostCenterCRUD
from app.api.v1.module_dimension.cost_center.service import CostCenterService
from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.dict.service import DictDataService
from app.common.constant import BUDGET_VERSION_DICT_TYPE
from app.core.exceptions import CustomException
from app.utils.excel_util import ExcelUtil

from .crud import BudgetDetailCRUD
from .schema import (
    BudgetDetailCreateSchema,
    BudgetDetailImportErrorSchema,
    BudgetDetailImportResultSchema,
    BudgetDetailOutSchema,
    BudgetDetailQueryParam,
    BudgetDetailUpdateSchema,
)


class BudgetDetailService:
    OUTPUT_PRELOAD = ["company", "accounting_subject", "cost_center"]
    IMPORT_ERROR_PREVIEW_LIMIT = 200

    @classmethod
    async def _get_budget_version_values(cls, redis: Redis) -> list[str]:
        options = await DictDataService.get_init_dict_service(
            redis=redis, dict_type=BUDGET_VERSION_DICT_TYPE
        )
        return [
            str(item["dict_value"]).strip()
            for item in options
            if item.get("dict_value") is not None
        ]

    @classmethod
    async def _validate_references(
        cls, auth: AuthSchema, data: BudgetDetailCreateSchema, redis: Redis
    ) -> None:
        budget_version_values = await cls._get_budget_version_values(redis)
        if data.budget_version not in budget_version_values:
            raise CustomException(msg=f"预算版本不在启用字典中: {data.budget_version}")

        company = await CompanyCRUD(auth).get_by_id_crud(data.company_id, preload=[])
        if not company:
            raise CustomException(msg="公司不存在")
        subject = await AccountingSubjectCRUD(auth).get_by_id_crud(
            data.accounting_subject_id, preload=[]
        )
        if not subject:
            raise CustomException(msg="会计科目不存在")
        if data.cost_center_id is not None:
            cost_center = await CostCenterCRUD(auth).get_by_id_crud(data.cost_center_id, preload=[])
            if not cost_center:
                raise CustomException(msg="成本中心不存在")
            if cost_center.company_id != data.company_id:
                raise CustomException(msg="成本中心不属于所选公司")

    @classmethod
    async def get_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        item = await BudgetDetailCRUD(auth).get_by_id_crud(id=id, preload=cls.OUTPUT_PRELOAD)
        if not item:
            raise CustomException(msg="预算明细不存在")
        return BudgetDetailOutSchema.model_validate(item).model_dump()

    @classmethod
    async def _prepare_search(
        cls, auth: AuthSchema, search: BudgetDetailQueryParam | None
    ) -> dict:
        search_dict = dict(search.__dict__) if search else {}
        department_ids = search_dict.pop("department_ids", [])
        if department_ids:
            cost_center_filter = search_dict.get("cost_center_id")
            selected_cost_center_ids = None
            if (
                isinstance(cost_center_filter, tuple)
                and len(cost_center_filter) == 2
                and cost_center_filter[0] == "in"
            ):
                selected_cost_center_ids = list(cost_center_filter[1])
            search_dict["cost_center_id"] = (
                "in",
                await CostCenterService.get_cost_center_ids_by_department_ids_service(
                    auth=auth,
                    department_ids=department_ids,
                    selected_cost_center_ids=selected_cost_center_ids,
                ),
            )
        return search_dict

    @classmethod
    async def get_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: BudgetDetailQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        search_dict = await cls._prepare_search(auth=auth, search=search)
        crud = BudgetDetailCRUD(auth)
        result = await crud.page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"year": "desc"}, {"id": "desc"}],
            search=search_dict,
            out_schema=BudgetDetailOutSchema,
            preload=cls.OUTPUT_PRELOAD,
        )
        result["amount_sum"] = await crud.sum_crud("amount", search=search_dict)
        return result

    @classmethod
    async def get_list_service(cls, auth: AuthSchema, search: BudgetDetailQueryParam | None = None) -> list[dict]:
        search_dict = await cls._prepare_search(auth=auth, search=search)
        items = await BudgetDetailCRUD(auth).get_list_crud(
            search=search_dict,
            order_by=[{"year": "desc"}, {"id": "desc"}],
            preload=cls.OUTPUT_PRELOAD,
        )
        return [BudgetDetailOutSchema.model_validate(item).model_dump() for item in items]

    @classmethod
    async def create_service(
        cls, auth: AuthSchema, data: BudgetDetailCreateSchema, redis: Redis
    ) -> dict:
        await cls._validate_references(auth, data, redis)
        crud = BudgetDetailCRUD(auth)
        item = await crud.create(data=data)
        return await cls.get_detail_service(auth, item.id)

    @classmethod
    async def update_service(
        cls, auth: AuthSchema, id: int, data: BudgetDetailUpdateSchema, redis: Redis
    ) -> dict:
        await cls._validate_references(auth, data, redis)
        crud = BudgetDetailCRUD(auth)
        if not await crud.get_by_id_crud(id=id, preload=[]):
            raise CustomException(msg="更新失败，预算明细不存在")
        item = await crud.update(id=id, data=data)
        return await cls.get_detail_service(auth, item.id)

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        crud = BudgetDetailCRUD(auth)
        for id in ids:
            if not await crud.get_by_id_crud(id=id, preload=[]):
                raise CustomException(msg="删除失败，预算明细不存在")
        await crud.delete(ids=ids)

    @classmethod
    async def get_import_template_service(cls, auth: AuthSchema, redis: Redis) -> bytes:
        """生成预算明细导入模板。"""

        header_list = [
            "预算版本",
            "年度",
            "公司代码",
            "会计科目代码",
            "成本中心代码",
            "归属月份",
            "币种",
            "金额",
            "预算文本",
            "数据来源分类",
            "数据来源说明",
        ]
        budget_version_values = await cls._get_budget_version_values(redis)
        selector_header_list = ["数据来源分类"]
        option_list = [{"数据来源分类": ["原始", "调整"]}]
        if budget_version_values:
            selector_header_list.insert(0, "预算版本")
            option_list.insert(0, {"预算版本": budget_version_values})

        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list,
        )

    @classmethod
    async def batch_import_service(
        cls, auth: AuthSchema, file: UploadFile, redis: Redis
    ) -> dict[str, Any]:
        """批量导入预算明细；每一行都会新增一条明细记录。"""

        header_dict = {
            "预算版本": "budget_version",
            "年度": "year",
            "公司代码": "company_code",
            "会计科目代码": "accounting_subject_code",
            "成本中心代码": "cost_center_code",
            "归属月份": "belonging_month",
            "币种": "currency",
            "金额": "amount",
            "预算文本": "budget_text",
            "数据来源分类": "data_source_category",
            "数据来源说明": "source_description",
        }

        try:
            filename = (file.filename or "").lower()
            if not filename.endswith((".xlsx", ".xls")):
                raise CustomException(
                    msg="仅支持 .xlsx 或 .xls 格式的 Excel 文件",
                    status_code=http_status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            try:
                contents = await file.read()
                df = pd.read_excel(io.BytesIO(contents))
            except Exception as error:
                raise CustomException(
                    msg="Excel 文件无法读取，请确认文件未损坏且格式正确",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                ) from error
            finally:
                await file.close()

            if df.empty:
                raise CustomException(
                    msg="导入文件为空",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            df.columns = [str(column).strip() for column in df.columns]
            missing_headers = [header for header in header_dict if header not in df.columns]
            if missing_headers:
                raise CustomException(
                    msg=f"导入文件缺少必要的列: {', '.join(missing_headers)}",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            df.rename(columns=header_dict, inplace=True)

            budget_version_values = await cls._get_budget_version_values(redis)
            total_count = len(df.index)
            created_count = 0
            failed_count = 0
            errors: list[BudgetDetailImportErrorSchema] = []
            errors_truncated = False
            budget_crud = BudgetDetailCRUD(auth)
            company_crud = CompanyCRUD(auth)
            subject_crud = AccountingSubjectCRUD(auth)
            cost_center_crud = CostCenterCRUD(auth)

            for row_number, (_index, row) in enumerate(df.iterrows(), start=2):
                budget_version: str | None = None
                try:
                    budget_version = cls._excel_text(row.get("budget_version"))
                    year_text = cls._excel_text(row.get("year"))
                    company_code = (cls._excel_text(row.get("company_code")) or "").upper()
                    subject_code = (
                        cls._excel_text(row.get("accounting_subject_code")) or ""
                    ).upper()
                    cost_center_code = (
                        cls._excel_text(row.get("cost_center_code")) or ""
                    ).upper()
                    raw_month = cls._excel_text(row.get("belonging_month"))
                    if not budget_version:
                        raise CustomException(msg="预算版本不能为空")
                    if budget_version not in budget_version_values:
                        raise CustomException(msg=f"预算版本不在启用字典中: {budget_version}")
                    if not year_text:
                        raise CustomException(msg="年度不能为空")
                    if not company_code:
                        raise CustomException(msg="公司代码不能为空")
                    if not subject_code:
                        raise CustomException(msg="会计科目代码不能为空")
                    if not raw_month:
                        raise CustomException(msg="归属月份不能为空")

                    year = cls._excel_int(year_text, "年度")
                    belonging_month = cls._excel_int(raw_month, "归属月份")
                    currency = (cls._excel_text(row.get("currency")) or "RMB").upper()
                    amount = cls._excel_decimal(row.get("amount"), "金额")
                    category = cls._excel_text(row.get("data_source_category")) or "原始"
                    if category not in {"原始", "调整"}:
                        raise CustomException(msg=f"数据来源分类不正确: {category}")

                    company = await company_crud.get(code=company_code, preload=[])
                    if not company:
                        raise CustomException(msg=f"公司不存在: {company_code}")
                    subject = await subject_crud.get(code=subject_code, preload=[])
                    if not subject:
                        raise CustomException(msg=f"会计科目不存在: {subject_code}")
                    cost_center_id: int | None = None
                    if cost_center_code:
                        cost_center = await cost_center_crud.get(
                            code=cost_center_code, preload=[]
                        )
                        if not cost_center:
                            raise CustomException(msg=f"成本中心不存在: {cost_center_code}")
                        if cost_center.company_id != company.id:
                            raise CustomException(msg="成本中心不属于所选公司")
                        cost_center_id = cost_center.id

                    payload = {
                        "budget_version": budget_version,
                        "year": year,
                        "company_id": company.id,
                        "accounting_subject_id": subject.id,
                        "cost_center_id": cost_center_id,
                        "belonging_month": belonging_month,
                        "currency": currency,
                        "amount": amount,
                        "budget_text": cls._excel_text(row.get("budget_text")),
                        "data_source_category": category,
                        "source_description": cls._excel_text(row.get("source_description")),
                    }

                    async with auth.db.begin_nested():
                        await budget_crud.create(data=BudgetDetailCreateSchema(**payload))
                        created_count += 1
                except Exception as error:
                    failed_count += 1
                    if len(errors) < cls.IMPORT_ERROR_PREVIEW_LIMIT:
                        errors.append(
                            BudgetDetailImportErrorSchema(
                                row_number=row_number,
                                budget_version=budget_version,
                                reason=str(error),
                            )
                        )
                    else:
                        errors_truncated = True

            result = BudgetDetailImportResultSchema(
                total_count=total_count,
                success_count=created_count,
                created_count=created_count,
                failed_count=failed_count,
                errors=errors,
                errors_truncated=errors_truncated,
            )
            if result.success_count == 0:
                raise CustomException(
                    msg="导入未成功：没有任何数据通过校验并写入系统",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    data=result.model_dump(),
                )
            return result.model_dump()
        except CustomException:
            raise
        except Exception as error:
            raise CustomException(
                msg="导入失败，请检查文件格式和数据内容",
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            ) from error

    @staticmethod
    def _excel_text(value: Any) -> str | None:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        text = str(value).strip()
        return text or None

    @classmethod
    def _excel_int(cls, value: str, field_name: str) -> int:
        try:
            return int(float(value))
        except ValueError as error:
            raise CustomException(msg=f"{field_name}格式不正确: {value}") from error

    @classmethod
    def _excel_decimal(cls, value: Any, field_name: str) -> Decimal:
        text = cls._excel_text(value)
        if not text:
            raise CustomException(msg=f"{field_name}不能为空")
        try:
            return Decimal(text.replace(",", ""))
        except InvalidOperation as error:
            raise CustomException(msg=f"{field_name}格式不正确: {text}") from error

    @classmethod
    async def export_service(cls, items: list[dict]) -> bytes:
        mapping = {
            "budget_version": "预算版本",
            "year": "年度",
            "company_code": "公司代码",
            "accounting_subject_code": "会计科目代码",
            "accounting_subject_name": "会计科目名称",
            "cost_center_code": "成本中心代码",
            "cost_center_name": "成本中心名称",
            "belonging_month": "归属月份",
            "currency": "币种",
            "amount": "金额",
            "budget_text": "预算文本",
            "data_source_category": "数据来源分类",
            "source_description": "数据来源说明",
        }
        return ExcelUtil.export_list2excel(items, mapping)
