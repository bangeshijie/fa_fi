"""预算业务模块路由。"""

from fastapi import APIRouter

from .budget_detail.controller import BudgetDetailRouter


budget_router = APIRouter(prefix="/budget")
budget_router.include_router(BudgetDetailRouter)

__all__ = ["budget_router"]
