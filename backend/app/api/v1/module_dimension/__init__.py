"""主数据模块路由。"""

from fastapi import APIRouter

from .company.controller import CompanyRouter
from .cost_center.controller import CostCenterRouter
from .accounting_subject.controller import AccountingSubjectRouter


dimension_router = APIRouter(prefix="/dimension")
dimension_router.include_router(CompanyRouter)
dimension_router.include_router(CostCenterRouter)
dimension_router.include_router(AccountingSubjectRouter)


__all__ = ["dimension_router"]
