"""
资产API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from ...core.database import get_db
from ...schemas.asset import AssetCreate, AssetRead, AssetUpdate
from ...schemas.common import (
    ResponseModel,
    PaginatedResponse,
    PaginatedData,
    PaginationMeta,
)
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
    return ResponseModel(data=AssetRead.model_validate(asset), message="资产创建成功")


@router.get("", response_model=PaginatedResponse[AssetRead], summary="获取资产列表")
async def get_assets(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[str] = Query(None, description="资产类型"),
    include_in_total: Optional[bool] = Query(None, description="是否计入总资产"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的资产列表"""
    # 构建查询条件
    conditions = [Asset.user_id == current_user.id]

    if type:
        conditions.append(Asset.type == type)
    if include_in_total is not None:
        conditions.append(Asset.include_in_total == include_in_total)

    # 计算偏移量
    offset = (page - 1) * size

    # 查询资产
    stmt = (
        select(Asset)
        .where(*conditions)
        .offset(offset)
        .limit(size)
        .order_by(Asset.created_at.desc())
    )
    result = await db.execute(stmt)
    assets = result.scalars().all()

    # 查询总数
    count_stmt = select(func.count(Asset.id)).where(*conditions)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 构建分页信息
    pages = (total + size - 1) // size
    pagination = PaginationMeta(
        page=page,
        size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )

    return PaginatedResponse(
        data=PaginatedData(
            items=[AssetRead.model_validate(asset) for asset in assets],
            pagination=pagination,
        )
    )


@router.get("/overview", response_model=ResponseModel[dict], summary="获取资产总览")
async def get_assets_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取资产总览统计"""
    # 查询用户所有资产
    stmt = select(Asset).where(Asset.user_id == current_user.id)
    result = await db.execute(stmt)
    assets = result.scalars().all()

    # 计算统计信息
    total_assets = sum(
        float(asset.balance)
        for asset in assets
        if asset.include_in_total and asset.balance >= 0
    )
    positive_assets = sum(
        float(asset.balance) for asset in assets if asset.balance >= 0
    )
    liabilities = abs(
        sum(float(asset.balance) for asset in assets if asset.balance < 0)
    )
    net_worth = positive_assets - liabilities
    asset_count = len(assets)
    liability_ratio = liabilities / positive_assets if positive_assets > 0 else 0

    # 按类型分组统计
    asset_breakdown = {}
    for asset in assets:
        asset_type = asset.type
        if asset_type not in asset_breakdown:
            asset_breakdown[asset_type] = {"count": 0, "total_balance": 0}
        asset_breakdown[asset_type]["count"] += 1
        asset_breakdown[asset_type]["total_balance"] += float(asset.balance)

    # 转换为列表格式并计算百分比
    breakdown_list = []
    for asset_type, data in asset_breakdown.items():
        percentage = (
            data["total_balance"] / positive_assets if positive_assets > 0 else 0
        )
        breakdown_list.append(
            {
                "type": asset_type,
                "count": data["count"],
                "total_balance": data["total_balance"],
                "percentage": percentage,
            }
        )

    overview = {
        "total_assets": total_assets,
        "positive_assets": positive_assets,
        "liabilities": liabilities,
        "net_worth": net_worth,
        "asset_count": asset_count,
        "liability_ratio": liability_ratio,
        "asset_breakdown": breakdown_list,
    }

    return ResponseModel(data=overview)


@router.get(
    "/{asset_id}", response_model=ResponseModel[AssetRead], summary="获取资产详情"
)
async def get_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取资产详情"""
    stmt = select(Asset).where(
        (Asset.id == asset_id) & (Asset.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资产不存在")

    return ResponseModel(data=AssetRead.model_validate(asset))


@router.put("/{asset_id}", response_model=ResponseModel[AssetRead], summary="更新资产")
async def update_asset(
    asset_id: uuid.UUID,
    asset_update: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新资产信息"""
    stmt = select(Asset).where(
        (Asset.id == asset_id) & (Asset.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资产不存在")

    # 更新资产信息
    update_data = asset_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)

    return ResponseModel(data=AssetRead.model_validate(asset), message="资产更新成功")


@router.delete("/{asset_id}", response_model=ResponseModel[dict], summary="删除资产")
async def delete_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除资产"""
    stmt = select(Asset).where(
        (Asset.id == asset_id) & (Asset.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资产不存在")

    await db.delete(asset)
    await db.commit()

    return ResponseModel(data={"id": str(asset_id)}, message="资产删除成功")
