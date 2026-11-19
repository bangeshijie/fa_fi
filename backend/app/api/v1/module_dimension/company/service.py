from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException
from app.utils.excel_util import ExcelUtil

from .crud import CompanyCRUD
from .schema import (
    CompanyCreateSchema,
    CompanyOptionSchema,
    CompanyOutSchema,
    CompanyQueryParam,
    CompanyUpdateSchema,
)


class CompanyService:
    """公司主数据服务层。"""

    COMPANY_OUTPUT_PRELOAD = ["holding_company"]

    @classmethod
    async def get_company_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        company = await CompanyCRUD(auth).get_by_id_crud(
            id=id, preload=cls.COMPANY_OUTPUT_PRELOAD
        )
        if not company:
            raise CustomException(msg="公司不存在")
        return CompanyOutSchema.model_validate(company).model_dump()

    @classmethod
    async def get_company_list_service(
        cls,
        auth: AuthSchema,
        search: CompanyQueryParam | None = None,
        order_by: list[dict] | None = None,
    ) -> list[dict]:
        company_list = await CompanyCRUD(auth).get_list_crud(
            search=search.__dict__ if search else {},
            order_by=order_by,
            preload=cls.COMPANY_OUTPUT_PRELOAD,
        )
        return [CompanyOutSchema.model_validate(item).model_dump() for item in company_list]

    @classmethod
    async def get_company_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: CompanyQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        return await CompanyCRUD(auth).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"updated_time": "desc"}],
            search=search.__dict__ if search else {},
            out_schema=CompanyOutSchema,
            preload=cls.COMPANY_OUTPUT_PRELOAD,
        )

    @classmethod
    async def get_company_options_service(cls, auth: AuthSchema) -> list[dict]:
        companies = await CompanyCRUD(auth).get_options_crud()
        return [CompanyOptionSchema.model_validate(item).model_dump() for item in companies]

    @classmethod
    async def validate_holding_company_service(
        cls, auth: AuthSchema, company_id: int | None, holding_company_id: int | None
    ) -> None:
        if holding_company_id is None:
            return
        if company_id == holding_company_id:
            raise CustomException(msg="上级控股公司不能选择自身")

        crud = CompanyCRUD(auth)
        current = await crud.get_by_id_crud(id=holding_company_id)
        if not current:
            raise CustomException(msg="上级控股公司不存在")

        visited: set[int] = set()
        while current and current.holding_company_id is not None:
            if current.id in visited:
                raise CustomException(msg="公司控股关系存在循环")
            visited.add(current.id)
            if company_id is not None and current.holding_company_id == company_id:
                raise CustomException(msg="公司控股关系不能形成循环")
            current = await crud.get_by_id_crud(id=current.holding_company_id)

    @classmethod
    async def create_company_service(cls, auth: AuthSchema, data: CompanyCreateSchema) -> dict:
        crud = CompanyCRUD(auth)
        await cls.validate_holding_company_service(auth, None, data.holding_company_id)
        if await crud.get(code=data.code):
            raise CustomException(msg="创建失败，公司代码已存在")
        if await crud.get(name=data.name):
            raise CustomException(msg="创建失败，公司名称已存在")
        if data.business_license_no and await crud.get(business_license_no=data.business_license_no):
            raise CustomException(msg="创建失败，营业执照号码已存在")
        company = await crud.create(data=data)
        company = await crud.get_by_id_crud(
            id=company.id, preload=cls.COMPANY_OUTPUT_PRELOAD
        )
        if not company:
            raise CustomException(msg="创建失败，公司保存后无法读取")
        return CompanyOutSchema.model_validate(company).model_dump()

    @classmethod
    async def update_company_service(
        cls, auth: AuthSchema, id: int, data: CompanyUpdateSchema
    ) -> dict:
        crud = CompanyCRUD(auth)
        company = await crud.get_by_id_crud(id=id)
        if not company:
            raise CustomException(msg="更新失败，公司不存在")
        await cls.validate_holding_company_service(auth, id, data.holding_company_id)
        existing = await crud.get(code=data.code)
        if existing and existing.id != id:
            raise CustomException(msg="更新失败，公司代码已存在")
        existing = await crud.get(name=data.name)
        if existing and existing.id != id:
            raise CustomException(msg="更新失败，公司名称已存在")
        if data.business_license_no:
            existing = await crud.get(business_license_no=data.business_license_no)
            if existing and existing.id != id:
                raise CustomException(msg="更新失败，营业执照号码已存在")
        company = await crud.update(id=id, data=data)
        company = await crud.get_by_id_crud(
            id=company.id, preload=cls.COMPANY_OUTPUT_PRELOAD
        )
        if not company:
            raise CustomException(msg="更新失败，公司保存后无法读取")
        return CompanyOutSchema.model_validate(company).model_dump()

    @classmethod
    async def delete_company_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        crud = CompanyCRUD(auth)
        for id in ids:
            if not await crud.get_by_id_crud(id=id):
                raise CustomException(msg="删除失败，公司不存在")
        await crud.delete(ids=ids)

    @classmethod
    async def set_company_available_service(
        cls, auth: AuthSchema, data: BatchSetAvailable
    ) -> None:
        if not data.ids:
            raise CustomException(msg="状态修改失败，操作对象不能为空")
        await CompanyCRUD(auth).set_available_crud(ids=data.ids, status=data.status)

    @classmethod
    async def export_company_list_service(cls, company_list: list[dict]) -> bytes:
        mapping_dict = {
            "id": "编号",
            "code": "公司代码",
            "name": "公司名称",
            "holding_company_code": "上级控股公司代码",
            "holding_company_name": "上级控股公司名称",
            "address": "公司地址",
            "phone": "公司电话",
            "business_license_no": "营业执照号码",
            "leader": "公司负责人",
            "holding_ratio": "控股比例(%)",
            "registered_capital": "注册资本(万元)",
            "status": "状态",
            "description": "备注",
            "created_time": "创建时间",
            "updated_time": "更新时间",
        }
        data = [item.copy() for item in company_list]
        for item in data:
            item["status"] = "正常" if item.get("status") == "0" else "停用"
        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)
