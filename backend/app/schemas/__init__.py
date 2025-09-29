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
from .debt import DebtCreate, DebtUpdate, DebtResponse, DebtSummary
from .report import (
    IncomeExpenseSummaryResponse,
    TrendAnalysisResponse,
    CategoryStatsResponse,
    ComparisonAnalysisResponse,
)
from .common import ResponseModel, PaginatedResponse, MessageResponse

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
    "DebtCreate",
    "DebtUpdate",
    "DebtResponse",
    "DebtSummary",
    "IncomeExpenseSummaryResponse",
    "TrendAnalysisResponse",
    "CategoryStatsResponse",
    "ComparisonAnalysisResponse",
    "ResponseModel",
    "PaginatedResponse",
    "MessageResponse",
]
