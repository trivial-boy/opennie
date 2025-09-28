"""
预算API路由
"""

from fastapi import APIRouter, Depends
from ...schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from ...schemas.common import ResponseModel
from ...models.user import User
from ...api.deps import get_current_user

router = APIRouter()


@router.post("", response_model=ResponseModel[BudgetRead], summary="创建预算")
async def create_budget(
    budget_data: BudgetCreate, current_user: User = Depends(get_current_user)
):
    """创建新预算"""
    # TODO: 实现预算创建
    return ResponseModel(data={}, message="预算创建成功")


@router.get("", response_model=ResponseModel[list], summary="获取预算列表")
async def get_budgets(current_user: User = Depends(get_current_user)):
    """获取预算列表"""
    # TODO: 实现预算列表查询
    return ResponseModel(data=[])
