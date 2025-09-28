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

api_router = APIRouter()

# 注册路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["账本"])
api_router.include_router(bills_router, prefix="/bills", tags=["账单"])
api_router.include_router(assets_router, prefix="/assets", tags=["资产"])
api_router.include_router(categories_router, prefix="/categories", tags=["分类"])
api_router.include_router(budgets_router, prefix="/budgets", tags=["预算"])
