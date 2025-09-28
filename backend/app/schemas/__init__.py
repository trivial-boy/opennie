"""
API数据模式模块
"""

from .user import UserCreate, UserRead, UserUpdate
from .auth import Token, LoginRequest, RegisterRequest, VerifyEmailRequest
from .account import AccountCreate, AccountRead, AccountUpdate
from .asset import AssetCreate, AssetRead, AssetUpdate
from .category import CategoryCreate, CategoryRead, CategoryUpdate
from .bill import BillCreate, BillRead, BillUpdate
from .budget import BudgetCreate, BudgetRead, BudgetUpdate
from .common import ResponseModel, PaginatedResponse

__all__ = [
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "Token",
    "LoginRequest",
    "RegisterRequest",
    "VerifyEmailRequest",
    "AccountCreate",
    "AccountRead",
    "AccountUpdate",
    "AssetCreate",
    "AssetRead",
    "AssetUpdate",
    "CategoryCreate",
    "CategoryRead",
    "CategoryUpdate",
    "BillCreate",
    "BillRead",
    "BillUpdate",
    "BudgetCreate",
    "BudgetRead",
    "BudgetUpdate",
    "ResponseModel",
    "PaginatedResponse",
]
