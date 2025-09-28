"""
账本API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from ...core.database import get_db
from ...schemas.account import AccountCreate, AccountRead, AccountUpdate, AccountSummary
from ...schemas.common import (
    ResponseModel,
    PaginatedResponse,
    PaginatedData,
    PaginationMeta,
)
from ...models.user import User
from ...models.account import Account
from ...models.bill import Bill
from ...api.deps import get_current_user
from datetime import date
import uuid

router = APIRouter()


@router.post("", response_model=ResponseModel[AccountRead], summary="创建账本")
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新账本"""
    account = Account(user_id=current_user.id, **account_data.dict())
    db.add(account)
    await db.commit()
    await db.refresh(account)

    return ResponseModel(
        data=AccountRead.model_validate(account), message="账本创建成功"
    )


@router.get("", response_model=PaginatedResponse[AccountRead], summary="获取账本列表")
async def get_accounts(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的账本列表"""
    # 计算偏移量
    offset = (page - 1) * size

    # 查询账本
    stmt = (
        select(Account)
        .where(Account.user_id == current_user.id)
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    accounts = result.scalars().all()

    # 查询总数
    count_stmt = select(func.count(Account.id)).where(
        Account.user_id == current_user.id
    )
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
            items=[AccountRead.model_validate(account) for account in accounts],
            pagination=pagination,
        )
    )


@router.get(
    "/{account_id}", response_model=ResponseModel[AccountRead], summary="获取账本详情"
)
async def get_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定账本的详情"""
    stmt = select(Account).where(
        (Account.id == account_id) & (Account.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账本不存在")

    return ResponseModel(data=AccountRead.model_validate(account))


@router.put(
    "/{account_id}", response_model=ResponseModel[AccountRead], summary="更新账本"
)
async def update_account(
    account_id: uuid.UUID,
    account_update: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新账本信息"""
    stmt = select(Account).where(
        (Account.id == account_id) & (Account.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账本不存在")

    # 更新账本信息
    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)

    return ResponseModel(
        data=AccountRead.model_validate(account), message="账本更新成功"
    )


@router.delete("/{account_id}", response_model=ResponseModel[dict], summary="删除账本")
async def delete_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除账本"""
    stmt = select(Account).where(
        (Account.id == account_id) & (Account.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账本不存在")

    await db.delete(account)
    await db.commit()

    return ResponseModel(data={"id": str(account_id)}, message="账本删除成功")


@router.get(
    "/{account_id}/summary",
    response_model=ResponseModel[AccountSummary],
    summary="获取账本汇总",
)
async def get_account_summary(
    account_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取账本收支汇总"""
    # 验证账本权限
    stmt = select(Account).where(
        (Account.id == account_id) & (Account.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账本不存在")

    # 构建查询条件
    conditions = [Bill.account_id == account_id]
    if start_date:
        conditions.append(Bill.date >= start_date)
    if end_date:
        conditions.append(Bill.date <= end_date)

    # 查询收支汇总
    income_stmt = select(func.coalesce(func.sum(Bill.amount), 0)).where(
        *conditions, Bill.type == "income"
    )
    expense_stmt = select(func.coalesce(func.sum(Bill.amount), 0)).where(
        *conditions, Bill.type == "expense"
    )
    count_stmt = select(func.count(Bill.id)).where(*conditions)

    income_result = await db.execute(income_stmt)
    expense_result = await db.execute(expense_stmt)
    count_result = await db.execute(count_stmt)

    total_income = float(income_result.scalar())
    total_expense = float(expense_result.scalar())
    transaction_count = count_result.scalar()

    summary = AccountSummary(
        total_income=total_income,
        total_expense=total_expense,
        net_amount=total_income - total_expense,
        transaction_count=transaction_count,
        period={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )

    return ResponseModel(data=summary)
