"""
分类API路由
"""

from fastapi import APIRouter, Depends
from ...schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from ...schemas.common import ResponseModel
from ...models.user import User
from ...api.deps import get_current_user

router = APIRouter()


@router.post("", response_model=ResponseModel[CategoryRead], summary="创建分类")
async def create_category(
    category_data: CategoryCreate, current_user: User = Depends(get_current_user)
):
    """创建新分类"""
    # TODO: 实现分类创建
    return ResponseModel(data={}, message="分类创建成功")


@router.get("", response_model=ResponseModel[list], summary="获取分类列表")
async def get_categories(current_user: User = Depends(get_current_user)):
    """获取分类列表"""
    # TODO: 实现分类列表查询
    return ResponseModel(data=[])
