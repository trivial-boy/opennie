"""
账单API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from ...core.database import get_db
from ...schemas.bill import (
    BillCreate,
    BillRead,
    BillUpdate,
    BillWithDetails,
    DailySummary,
)
from ...schemas.common import (
    ResponseModel,
    PaginatedResponse,
    PaginatedData,
    PaginationMeta,
)
from ...models.user import User
from ...models.bill import Bill
from ...models.account import Account
from ...models.asset import Asset
from ...models.category import Category
from ...api.deps import get_current_user
from datetime import date
import uuid

router = APIRouter()


@router.post("", response_model=ResponseModel[BillRead], summary="创建账单")
async def create_bill(
    bill_data: BillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新账单"""
    # 验证账本权限
    stmt = select(Account).where(
        (Account.id == bill_data.account_id) & (Account.user_id == current_user.id)
    )
    account = await db.execute(stmt)
    if not account.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="账本不存在或无权限"
        )

    bill = Bill(user_id=current_user.id, **bill_data.dict())
    db.add(bill)
    await db.commit()
    await db.refresh(bill)

    return ResponseModel(data=BillRead.from_orm(bill), message="账单创建成功")


@router.get(
    "", response_model=PaginatedResponse[BillWithDetails], summary="获取账单列表"
)
async def get_bills(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    account_id: Optional[uuid.UUID] = Query(None, description="账本ID"),
    type: Optional[str] = Query(None, description="账单类型"),
    category_id: Optional[uuid.UUID] = Query(None, description="分类ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取账单列表"""
    # 构建查询条件
    conditions = [Bill.user_id == current_user.id]

    if account_id:
        conditions.append(Bill.account_id == account_id)
    if type:
        conditions.append(Bill.type == type)
    if category_id:
        conditions.append(Bill.category_id == category_id)
    if start_date:
        conditions.append(Bill.date >= start_date)
    if end_date:
        conditions.append(Bill.date <= end_date)

    # 计算偏移量
    offset = (page - 1) * size

    # 查询账单（关联查询）
    stmt = (
        select(Bill, Account, Asset, Category)
        .join(Account, Bill.account_id == Account.id)
        .join(Asset, Bill.asset_id == Asset.id)
        .join(Category, Bill.category_id == Category.id)
        .where(and_(*conditions))
        .order_by(Bill.date.desc(), Bill.created_at.desc())
        .offset(offset)
        .limit(size)
    )

    result = await db.execute(stmt)
    bills_data = result.all()

    # 查询总数
    count_stmt = select(func.count(Bill.id)).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 构建响应数据
    bills_with_details = []
    for bill, account, asset, category in bills_data:
        bill_dict = BillRead.from_orm(bill).dict()
        bill_dict.update(
            {
                "account": {"id": str(account.id), "name": account.name},
                "asset": {"id": str(asset.id), "name": asset.name, "type": asset.type},
                "category": {
                    "id": str(category.id),
                    "name": category.name,
                    "icon": category.icon,
                    "color": category.color,
                },
            }
        )
        bills_with_details.append(bill_dict)

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
        data=PaginatedData(items=bills_with_details, pagination=pagination)
    )


@router.get(
    "/{bill_id}", response_model=ResponseModel[BillWithDetails], summary="获取账单详情"
)
async def get_bill(
    bill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取账单详情"""
    stmt = (
        select(Bill, Account, Asset, Category)
        .join(Account, Bill.account_id == Account.id)
        .join(Asset, Bill.asset_id == Asset.id)
        .join(Category, Bill.category_id == Category.id)
        .where((Bill.id == bill_id) & (Bill.user_id == current_user.id))
    )

    result = await db.execute(stmt)
    bill_data = result.first()

    if not bill_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")

    bill, account, asset, category = bill_data
    bill_dict = BillRead.from_orm(bill).dict()
    bill_dict.update(
        {
            "account": {"id": str(account.id), "name": account.name},
            "asset": {"id": str(asset.id), "name": asset.name, "type": asset.type},
            "category": {
                "id": str(category.id),
                "name": category.name,
                "icon": category.icon,
                "color": category.color,
            },
        }
    )

    return ResponseModel(data=bill_dict)


@router.put("/{bill_id}", response_model=ResponseModel[BillRead], summary="更新账单")
async def update_bill(
    bill_id: uuid.UUID,
    bill_update: BillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新账单"""
    stmt = select(Bill).where((Bill.id == bill_id) & (Bill.user_id == current_user.id))
    result = await db.execute(stmt)
    bill = result.scalar_one_or_none()

    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")

    # 更新账单
    update_data = bill_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bill, field, value)

    await db.commit()
    await db.refresh(bill)

    return ResponseModel(data=BillRead.from_orm(bill), message="账单更新成功")


@router.delete("/{bill_id}", response_model=ResponseModel[dict], summary="删除账单")
async def delete_bill(
    bill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除账单"""
    stmt = select(Bill).where((Bill.id == bill_id) & (Bill.user_id == current_user.id))
    result = await db.execute(stmt)
    bill = result.scalar_one_or_none()

    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")

    await db.delete(bill)
    await db.commit()

    return ResponseModel(data={"id": str(bill_id)}, message="账单删除成功")
