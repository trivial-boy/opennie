"""
API v1版本
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .accounts import router as accounts_router
from .bills import router as bills_router
from .assets import router as assets_router
from .categories import router as categories_router
from .budgets import router as budgets_router
from .debts import router as debts_router
from .recurring_bills import router as recurring_bills_router
from .reports_fixed import router as reports_router
from .reports_simple import router as reports_simple_router
from .ocr import router as ocr_router
from .sql import router as sql_router

api_router = APIRouter()

# 注册路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["账本"])
api_router.include_router(bills_router, prefix="/bills", tags=["账单"])
api_router.include_router(assets_router, prefix="/assets", tags=["资产"])
api_router.include_router(categories_router, prefix="/categories", tags=["分类"])
api_router.include_router(budgets_router, prefix="/budgets", tags=["预算"])
api_router.include_router(debts_router, prefix="/debts", tags=["债务管理"])
api_router.include_router(
    recurring_bills_router, prefix="/recurring-bills", tags=["周期账单"]
)
api_router.include_router(reports_router, prefix="/reports", tags=["报表统计"])
api_router.include_router(
    reports_simple_router, prefix="/reports-simple", tags=["报表统计-简化测试"]
)
api_router.include_router(ocr_router, tags=["OCR图像识别"])
api_router.include_router(sql_router, prefix="/sql", tags=["SQL查询"])
