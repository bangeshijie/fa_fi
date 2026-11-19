import io
from typing import Any

import pandas as pd
from fastapi import UploadFile, status as http_status

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException
from app.utils.excel_util import ExcelUtil

from .crud import AccountingSubjectCRUD
from .schema import (
    AccountingSubjectCreateSchema,
    AccountingSubjectImportErrorSchema,
    AccountingSubjectImportResultSchema,
    AccountingSubjectOutSchema,
    AccountingSubjectCategoryOptionSchema,
    AccountingSubjectOptionSchema,
    AccountingSubjectQueryParam,
    AccountingSubjectUpdateSchema,
)


class AccountingSubjectService:
    """会计科目主数据服务层。"""

    OUTPUT_PRELOAD = ["created_by", "updated_by", "deleted_by"]
    IMPORT_ERROR_PREVIEW_LIMIT = 200

    @classmethod
    async def get_options_service(cls, auth: AuthSchema) -> list[dict]:
        items = await AccountingSubjectCRUD(auth).get_list_crud(
            search={"status": ("eq", "0")},
            order_by=[{"code": "asc"}],
            preload=[],
        )
        return [AccountingSubjectOptionSchema.model_validate(item).model_dump() for item in items]

    @classmethod
    async def get_category_options_service(
        cls, auth: AuthSchema
    ) -> list[dict]:
        """从现有会计科目三级字段组装管理分类树。"""

        items = await AccountingSubjectCRUD(auth).get_list_crud(
            order_by=[
                {"management_category_level1": "asc"},
                {"management_category_level2": "asc"},
                {"management_category_level3": "asc"},
            ],
            preload=[],
        )
        tree: dict[str, dict[str, Any]] = {}

        for item in items:
            levels = [
                (item.management_category_level1 or "").strip(),
                (item.management_category_level2 or "").strip(),
                (item.management_category_level3 or "").strip(),
            ]
            if not levels[0]:
                continue

            current = tree
            for level in levels:
                if not level:
                    break
                node = current.setdefault(
                    level,
                    {"value": level, "label": level, "children": {}},
                )
                current = node["children"]

        def serialize(nodes: dict[str, dict[str, Any]]) -> list[dict]:
            return [
                AccountingSubjectCategoryOptionSchema(
                    value=node["value"],
                    label=node["label"],
                    children=serialize(node["children"]),
                ).model_dump()
                for node in nodes.values()
            ]

        return serialize(tree)

    @classmethod
    async def get_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        item = await AccountingSubjectCRUD(auth).get_by_id_crud(
            id=id, preload=cls.OUTPUT_PRELOAD
        )
        if not item:
            raise CustomException(msg="会计科目不存在")
        return AccountingSubjectOutSchema.model_validate(item).model_dump()

    @classmethod
    async def get_list_service(
        cls,
        auth: AuthSchema,
        search: AccountingSubjectQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[dict]:
        items = await AccountingSubjectCRUD(auth).get_list_crud(
            search=search.__dict__ if search else {},
            order_by=order_by,
            preload=cls.OUTPUT_PRELOAD,
        )
        return [AccountingSubjectOutSchema.model_validate(item).model_dump() for item in items]

    @classmethod
    async def get_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: AccountingSubjectQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        return await AccountingSubjectCRUD(auth).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"updated_time": "desc"}],
            search=search.__dict__ if search else {},
            out_schema=AccountingSubjectOutSchema,
            preload=cls.OUTPUT_PRELOAD,
        )

    @classmethod
    async def create_service(
        cls, auth: AuthSchema, data: AccountingSubjectCreateSchema
    ) -> dict:
        crud = AccountingSubjectCRUD(auth)
        if await crud.get(code=data.code):
            raise CustomException(msg="创建失败，会计科目代码已存在")
        item = await crud.create(data=data)
        item = await crud.get_by_id_crud(id=item.id, preload=cls.OUTPUT_PRELOAD)
        if not item:
            raise CustomException(msg="创建失败，会计科目保存后无法读取")
        return AccountingSubjectOutSchema.model_validate(item).model_dump()

    @classmethod
    async def update_service(
        cls, auth: AuthSchema, id: int, data: AccountingSubjectUpdateSchema
    ) -> dict:
        crud = AccountingSubjectCRUD(auth)
        if not await crud.get_by_id_crud(id=id, preload=[]):
            raise CustomException(msg="更新失败，会计科目不存在")
        existing = await crud.get(code=data.code)
        if existing and existing.id != id:
            raise CustomException(msg="更新失败，会计科目代码已存在")
        item = await crud.update(id=id, data=data)
        item = await crud.get_by_id_crud(id=item.id, preload=cls.OUTPUT_PRELOAD)
        if not item:
            raise CustomException(msg="更新失败，会计科目保存后无法读取")
        return AccountingSubjectOutSchema.model_validate(item).model_dump()

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        crud = AccountingSubjectCRUD(auth)
        for id in ids:
            if not await crud.get_by_id_crud(id=id, preload=[]):
                raise CustomException(msg="删除失败，会计科目不存在")
        await crud.delete(ids=ids)

    @classmethod
    async def set_available_service(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        if not data.ids:
            raise CustomException(msg="状态修改失败，操作对象不能为空")
        if data.status not in {"0", "1"}:
            raise CustomException(msg="状态参数不正确")
        await AccountingSubjectCRUD(auth).set_available_crud(
            ids=data.ids, status=data.status
        )

    @classmethod
    async def get_import_template_service(cls, auth: AuthSchema) -> bytes:
        """生成会计科目导入模板。"""

        header_list = [
            "会计科目代码",
            "会计科目名称",
            "科目余额方向",
            "所属会计报表科目",
            "管理三级分类",
            "管理科目一级分类",
            "管理科目二级分类",
            "科目负责人",
            "状态",
            "备注",
        ]
        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=["科目余额方向", "状态"],
            option_list=[
                {"科目余额方向": ["借", "贷"]},
                {"状态": ["正常", "停用"]},
            ],
        )

    @classmethod
    async def batch_import_service(
        cls, auth: AuthSchema, file: UploadFile
    ) -> dict[str, Any]:
        """批量导入会计科目；代码已存在时更新该记录。"""

        header_dict = {
            "会计科目代码": "code",
            "会计科目名称": "name",
            "科目余额方向": "balance_direction",
            "所属会计报表科目": "accounting_statement_subject",
            "管理三级分类": "management_category_level3",
            "管理科目一级分类": "management_category_level1",
            "管理科目二级分类": "management_category_level2",
            "科目负责人": "leader",
            "状态": "status",
            "备注": "description",
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
            missing_headers = [
                header for header in header_dict if header not in df.columns
            ]
            if missing_headers:
                raise CustomException(
                    msg=f"导入文件缺少必要的列: {', '.join(missing_headers)}",
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            df.rename(columns=header_dict, inplace=True)

            total_count = len(df.index)
            created_count = 0
            updated_count = 0
            duplicate_count = 0
            failed_count = 0
            errors: list[AccountingSubjectImportErrorSchema] = []
            errors_truncated = False
            subject_crud = AccountingSubjectCRUD(auth)

            for row_number, (_index, row) in enumerate(df.iterrows(), start=2):
                code: str | None = None
                try:
                    code = (cls._excel_text(row.get("code")) or "").upper()
                    name = cls._excel_text(row.get("name"))
                    if not code:
                        raise CustomException(msg="会计科目代码不能为空")
                    if not name:
                        raise CustomException(msg="会计科目名称不能为空")
                    balance_direction = cls._excel_text(row.get("balance_direction"))
                    if not balance_direction:
                        raise CustomException(msg="科目余额方向不能为空")

                    raw_status = cls._excel_text(row.get("status")) or "正常"
                    status_map = {
                        "正常": "0",
                        "启用": "0",
                        "0": "0",
                        "停用": "1",
                        "禁用": "1",
                        "1": "1",
                    }
                    status = status_map.get(raw_status)
                    if status is None:
                        raise CustomException(
                            msg=f"状态只能填写正常/停用，当前值: {raw_status}"
                        )

                    payload = {
                        "code": code,
                        "name": name,
                        "balance_direction": balance_direction,
                        "accounting_statement_subject": cls._excel_text(
                            row.get("accounting_statement_subject")
                        ),
                        "management_category_level3": cls._excel_text(
                            row.get("management_category_level3")
                        ),
                        "management_category_level1": cls._excel_text(
                            row.get("management_category_level1")
                        ),
                        "management_category_level2": cls._excel_text(
                            row.get("management_category_level2")
                        ),
                        "leader": cls._excel_text(row.get("leader")),
                        "status": status,
                        "description": cls._excel_text(row.get("description")),
                    }

                    async with auth.db.begin_nested():
                        existing = await subject_crud.get(code=code, preload=[])
                        if existing:
                            duplicate_count += 1
                            await subject_crud.update(
                                id=existing.id,
                                data=AccountingSubjectUpdateSchema(**payload),
                            )
                            updated_count += 1
                        else:
                            await subject_crud.create(
                                data=AccountingSubjectCreateSchema(**payload)
                            )
                            created_count += 1
                except Exception as error:
                    failed_count += 1
                    if len(errors) < cls.IMPORT_ERROR_PREVIEW_LIMIT:
                        errors.append(
                            AccountingSubjectImportErrorSchema(
                                row_number=row_number,
                                code=code or None,
                                reason=str(error),
                            )
                        )
                    else:
                        errors_truncated = True

            result = AccountingSubjectImportResultSchema(
                total_count=total_count,
                success_count=created_count + updated_count,
                created_count=created_count,
                updated_count=updated_count,
                duplicate_count=duplicate_count,
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
    async def export_service(cls, items: list[dict]) -> bytes:
        mapping_dict = {
            "id": "编号",
            "code": "会计科目代码",
            "name": "会计科目名称",
            "balance_direction": "科目余额方向",
            "accounting_statement_subject": "所属会计报表科目",
            "management_category_level3": "管理三级分类",
            "management_category_level1": "管理科目一级分类",
            "management_category_level2": "管理科目二级分类",
            "leader": "科目负责人",
            "status": "状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
        }
        data = [item.copy() for item in items]
        for item in data:
            item["status"] = "正常" if item.get("status") == "0" else "停用"
        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)
