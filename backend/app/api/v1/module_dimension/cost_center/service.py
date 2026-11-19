import io
from datetime import date, datetime
from typing import Any

import pandas as pd
from fastapi import UploadFile, status as http_status
from redis.asyncio.client import Redis

from app.api.v1.module_dimension.company.crud import CompanyCRUD
from app.api.v1.module_system.dict.service import DictDataService
from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.constant import COST_CENTER_FUNCTION_SCOPE_DICT_TYPE
from app.api.v1.module_system.dept.crud import DeptCRUD
from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException
from app.utils.excel_util import ExcelUtil

from .crud import CostCenterCRUD
from .schema import (
    CostCenterCreateSchema,
    CostCenterImportErrorSchema,
    CostCenterImportResultSchema,
    CostCenterOptionSchema,
    CostCenterOutSchema,
    CostCenterQueryParam,
    CostCenterUpdateSchema,
    DepartmentOptionSchema,
)


class CostCenterService:
    """成本中心主数据服务层。"""

    OUTPUT_PRELOAD = ["company", "department"]
    IMPORT_ERROR_PREVIEW_LIMIT = 200

    @classmethod
    async def get_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        item = await CostCenterCRUD(auth).get_by_id_crud(id=id, preload=cls.OUTPUT_PRELOAD)
        if not item:
            raise CustomException(msg="成本中心不存在")
        return CostCenterOutSchema.model_validate(item).model_dump()

    @classmethod
    async def get_list_service(
        cls,
        auth: AuthSchema,
        search: CostCenterQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[dict]:
        items = await CostCenterCRUD(auth).get_list_crud(
            search=search.__dict__ if search else {},
            order_by=order_by,
            preload=cls.OUTPUT_PRELOAD,
        )
        return [CostCenterOutSchema.model_validate(item).model_dump() for item in items]

    @classmethod
    async def get_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: CostCenterQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        return await CostCenterCRUD(auth).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"updated_time": "desc"}],
            search=search.__dict__ if search else {},
            out_schema=CostCenterOutSchema,
            preload=cls.OUTPUT_PRELOAD,
        )

    @classmethod
    async def get_options_service(cls, auth: AuthSchema) -> list[dict]:
        items = await CostCenterCRUD(auth).get_list_crud(
            order_by=[{"code": "asc"}], preload=[]
        )
        return [CostCenterOptionSchema.model_validate(item).model_dump() for item in items]

    @classmethod
    async def get_department_options_service(cls, auth: AuthSchema) -> list[dict]:
        items = await DeptCRUD(auth).get_list_crud(
            order_by=[{"code": "asc"}], preload=[]
        )
        return [
            DepartmentOptionSchema(
                id=item.id, code=item.code, name=item.name, parent_id=item.parent_id
            ).model_dump()
            for item in items
        ]

    @classmethod
    async def get_cost_center_ids_by_department_ids_service(
        cls,
        auth: AuthSchema,
        department_ids: list[int],
        selected_cost_center_ids: list[int] | None = None,
    ) -> list[int]:
        """根据部门树筛选成本中心，并与已选成本中心取交集。"""

        selected_departments = {int(item) for item in department_ids if int(item) > 0}
        if not selected_departments:
            return sorted({int(item) for item in selected_cost_center_ids or [] if int(item) > 0})

        departments = await DeptCRUD(auth).get_list_crud(search={}, preload=[])
        parent_map = {int(item.id): item.parent_id for item in departments}
        children_map: dict[int, set[int]] = {}
        for department_id, parent_id in parent_map.items():
            if parent_id is not None:
                children_map.setdefault(int(parent_id), set()).add(department_id)

        expanded_departments = selected_departments & set(parent_map)
        pending = list(expanded_departments)
        while pending:
            current_id = pending.pop()
            for child_id in children_map.get(current_id, set()):
                if child_id not in expanded_departments:
                    expanded_departments.add(child_id)
                    pending.append(child_id)

        cost_centers = await CostCenterCRUD(auth).get_list_crud(
            search={"dept_id": ("in", sorted(expanded_departments))}, preload=[]
        )
        department_cost_center_ids = {int(item.id) for item in cost_centers}
        if selected_cost_center_ids is not None:
            department_cost_center_ids.intersection_update(
                int(item) for item in selected_cost_center_ids if int(item) > 0
            )
        return sorted(department_cost_center_ids)

    @classmethod
    async def validate_relations_service(
        cls, auth: AuthSchema, company_id: int, dept_id: int
    ) -> None:
        if not await CompanyCRUD(auth).get(id=company_id, preload=[]):
            raise CustomException(msg="所属公司不存在")
        if not await DeptCRUD(auth).get(id=dept_id, preload=[]):
            raise CustomException(msg="所属组织不存在")

    @classmethod
    async def create_service(cls, auth: AuthSchema, data: CostCenterCreateSchema) -> dict:
        crud = CostCenterCRUD(auth)
        await cls.validate_relations_service(auth, data.company_id, data.dept_id)
        if await crud.get(code=data.code):
            raise CustomException(msg="创建失败，成本中心代码已存在")
        item = await crud.create(data=data)
        item = await crud.get_by_id_crud(id=item.id, preload=cls.OUTPUT_PRELOAD)
        if not item:
            raise CustomException(msg="创建失败，成本中心保存后无法读取")
        return CostCenterOutSchema.model_validate(item).model_dump()

    @classmethod
    async def update_service(
        cls, auth: AuthSchema, id: int, data: CostCenterUpdateSchema
    ) -> dict:
        crud = CostCenterCRUD(auth)
        if not await crud.get_by_id_crud(id=id, preload=[]):
            raise CustomException(msg="更新失败，成本中心不存在")
        await cls.validate_relations_service(auth, data.company_id, data.dept_id)
        existing = await crud.get(code=data.code)
        if existing and existing.id != id:
            raise CustomException(msg="更新失败，成本中心代码已存在")
        item = await crud.update(id=id, data=data)
        item = await crud.get_by_id_crud(id=item.id, preload=cls.OUTPUT_PRELOAD)
        if not item:
            raise CustomException(msg="更新失败，成本中心保存后无法读取")
        return CostCenterOutSchema.model_validate(item).model_dump()

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        crud = CostCenterCRUD(auth)
        for id in ids:
            if not await crud.get_by_id_crud(id=id, preload=[]):
                raise CustomException(msg="删除失败，成本中心不存在")
        await crud.delete(ids=ids)

    @classmethod
    async def set_available_service(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        if not data.ids:
            raise CustomException(msg="状态修改失败，操作对象不能为空")
        if data.status not in {"0", "1"}:
            raise CustomException(msg="状态参数不正确")
        await CostCenterCRUD(auth).set_available_crud(ids=data.ids, status=data.status)

    @classmethod
    async def get_import_template_service(cls, auth: AuthSchema, redis: Redis) -> bytes:
        """生成成本中心导入模板。"""

        header_list = [
            "成本中心代码",
            "成本中心名称",
            "所属公司代码",
            "职能范围",
            "所属组织代码",
            "成本中心负责人",
            "启用日期",
            "状态",
            "备注",
        ]
        function_scope_options = await DictDataService.get_init_dict_service(
            redis=redis, dict_type=COST_CENTER_FUNCTION_SCOPE_DICT_TYPE
        )
        function_scope_values = [
            str(item["dict_value"])
            for item in function_scope_options
            if item.get("dict_value")
        ]
        selector_header_list = ["状态"]
        option_list = [{"状态": ["正常", "停用"]}]
        if function_scope_values:
            selector_header_list.insert(0, "职能范围")
            option_list.insert(0, {"职能范围": function_scope_values})

        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list,
        )

    @classmethod
    async def batch_import_service(cls, auth: AuthSchema, file: UploadFile) -> dict[str, Any]:
        """批量导入成本中心，按代码更新已存在数据。"""

        header_dict = {
            "成本中心代码": "code",
            "成本中心名称": "name",
            "所属公司代码": "company_code",
            "职能范围": "function_scope",
            "所属组织代码": "dept_code",
            "成本中心负责人": "leader",
            "启用日期": "enable_time",
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
            missing_headers = [header for header in header_dict if header not in df.columns]
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
            errors: list[CostCenterImportErrorSchema] = []
            errors_truncated = False
            cost_center_crud = CostCenterCRUD(auth)

            for row_number, (_index, row) in enumerate(df.iterrows(), start=2):
                code: str | None = None
                try:
                    code = (cls._excel_text(row.get("code")) or "").upper()
                    name = cls._excel_text(row.get("name"))
                    company_code = (cls._excel_text(row.get("company_code")) or "").upper()
                    function_scope = cls._excel_text(row.get("function_scope"))
                    dept_code = (cls._excel_text(row.get("dept_code")) or "").upper()
                    if not code:
                        raise CustomException(msg="成本中心代码不能为空")
                    if not name:
                        raise CustomException(msg="成本中心名称不能为空")
                    if not company_code:
                        raise CustomException(msg="所属公司代码不能为空")
                    if not dept_code:
                        raise CustomException(msg="所属组织代码不能为空")

                    company = await CompanyCRUD(auth).get(code=company_code, preload=[])
                    if not company:
                        raise CustomException(msg=f"所属公司不存在: {company_code}")
                    department = await DeptCRUD(auth).get(code=dept_code, preload=[])
                    if not department:
                        raise CustomException(msg=f"所属组织不存在: {dept_code}")

                    raw_enable_time = row.get("enable_time")
                    enable_time = cls._excel_date(raw_enable_time)
                    raw_status = cls._excel_text(row.get("status")) or "正常"
                    status_map = {"正常": "0", "启用": "0", "0": "0", "停用": "1", "禁用": "1", "1": "1"}
                    status = status_map.get(raw_status)
                    if status is None:
                        raise CustomException(msg=f"状态只能填写正常/停用，当前值: {raw_status}")

                    payload = {
                        "code": code,
                        "name": name,
                        "company_id": company.id,
                        "function_scope": function_scope,
                        "dept_id": department.id,
                        "leader": cls._excel_text(row.get("leader")),
                        "enable_time": enable_time,
                        "status": status,
                        "description": cls._excel_text(row.get("description")),
                    }

                    async with auth.db.begin_nested():
                        existing = await cost_center_crud.get(code=code, preload=[])
                        if existing:
                            duplicate_count += 1
                            await cost_center_crud.update(
                                id=existing.id, data=CostCenterUpdateSchema(**payload)
                            )
                            updated_count += 1
                        else:
                            await cost_center_crud.create(data=CostCenterCreateSchema(**payload))
                            created_count += 1
                except Exception as error:
                    failed_count += 1
                    if len(errors) < cls.IMPORT_ERROR_PREVIEW_LIMIT:
                        errors.append(
                            CostCenterImportErrorSchema(
                                row_number=row_number, code=code or None, reason=str(error)
                            )
                        )
                    else:
                        errors_truncated = True

            result = CostCenterImportResultSchema(
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
    def _excel_date(cls, value: Any) -> date:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            raise CustomException(msg="启用日期不能为空")
        if isinstance(value, pd.Timestamp):
            return value.date()
        if isinstance(value, datetime):
            return value.date()
        text = cls._excel_text(value)
        if not text:
            raise CustomException(msg="启用日期不能为空")
        try:
            return date.fromisoformat(text.replace("/", "-").split(" ", 1)[0])
        except ValueError as error:
            raise CustomException(msg=f"启用日期格式不正确: {text}") from error

    @classmethod
    async def export_service(cls, items: list[dict]) -> bytes:
        mapping_dict = {
            "id": "编号",
            "code": "成本中心代码",
            "name": "成本中心名称",
            "company_code": "所属公司代码",
            "company_name": "所属公司名称",
            "function_scope": "职能范围",
            "dept_code": "所属组织代码",
            "dept_name": "所属组织名称",
            "leader": "成本中心负责人",
            "enable_time": "启用日期",
            "status": "状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
        }
        data = [item.copy() for item in items]
        for item in data:
            item["status"] = "正常" if item.get("status") == "0" else "停用"
        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)
