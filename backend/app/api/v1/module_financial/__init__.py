"""财务业务模块路由。"""

from fastapi import APIRouter

from .accounting_voucher_detail.controller import AccountingVoucherDetailRouter
from .expense_analysis.controller import ExpenseAnalysisRouter
from .management_finance_variance.controller import ManagementFinanceVarianceRouter


financial_router = APIRouter(prefix="/financial")
financial_router.include_router(AccountingVoucherDetailRouter)
financial_router.include_router(ExpenseAnalysisRouter)
financial_router.include_router(ManagementFinanceVarianceRouter)

__all__ = ["financial_router"]
