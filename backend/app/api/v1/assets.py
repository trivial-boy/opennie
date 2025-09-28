"""
资产API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...schemas.asset import AssetCreate, AssetRead, AssetUpdate
from ...schemas.common import ResponseModel
from ...models.user import User
from ...models.asset import Asset
from ...api.deps import get_current_user
import uuid

router = APIRouter()


@router.post("", response_model=ResponseModel[AssetRead], summary="创建资产")
async def create_asset(
    asset_data: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新资产"""
    asset = Asset(user_id=current_user.id, **asset_data.dict())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return ResponseModel(data=AssetRead.from_orm(asset), message="资产创建成功")


@router.get("", response_model=ResponseModel[list], summary="获取资产列表")
async def get_assets(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """获取用户的资产列表"""
    # TODO: 实现资产列表查询
    return ResponseModel(data=[])


@router.get(
    "/{asset_id}", response_model=ResponseModel[AssetRead], summary="获取资产详情"
)
async def get_asset(asset_id: uuid.UUID):
    """获取资产详情"""
    # TODO: 实现资产详情查询
    return ResponseModel(data={})
