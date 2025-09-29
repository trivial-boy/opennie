"""
债务管理API路由
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case

from ...core.database import get_db
from ...models.user import User
from ...models.debt import Debt, DebtTypeEnum
from ...schemas.debt import (
    DebtCreate,
    DebtUpdate,
    DebtSettle,
    DebtResponse,
    DebtListResponse,
    DebtSummary,
    DebtQueryParams,
)
from ...schemas.common import MessageResponse, PaginatedResponse
from ...utils.pagination_params import PaginationParams
from ...utils.pagination_helpers import paginate_query, paginate_response
from ..deps import get_current_user

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[DebtResponse])
async def get_debts(
    pagination: PaginationParams = Depends(),
    type: Optional[DebtTypeEnum] = Query(None, description="债务类型筛选"),
    is_settled: Optional[bool] = Query(None, description="结清状态筛选"),
    counterpart: Optional[str] = Query(None, description="对方姓名筛选"),
    due_date_from: Optional[date] = Query(None, description="到期日期起始"),
    due_date_to: Optional[date] = Query(None, description="到期日期结束"),
    amount_min: Optional[Decimal] = Query(None, ge=0, description="最小金额"),
    amount_max: Optional[Decimal] = Query(None, ge=0, description="最大金额"),
    overdue_only: bool = Query(False, description="只显示逾期债务"),
    due_soon_only: bool = Query(False, description="只显示即将到期债务"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取债务列表"""
    query = select(Debt).where(Debt.user_id == current_user.id)

    # 应用筛选条件
    if type:
        query = query.where(Debt.type == type)

    if is_settled is not None:
        query = query.where(Debt.is_settled == is_settled)

    if counterpart:
        query = query.where(Debt.counterpart.ilike(f"%{counterpart}%"))

    if due_date_from:
        query = query.where(Debt.due_date >= due_date_from)

    if due_date_to:
        query = query.where(Debt.due_date <= due_date_to)

    if amount_min is not None:
        query = query.where(Debt.amount >= amount_min)

    if amount_max is not None:
        query = query.where(Debt.amount <= amount_max)

    # 逾期债务筛选
    if overdue_only:
        today = date.today()
        query = query.where(and_(Debt.due_date < today, Debt.is_settled == False))

    # 即将到期债务筛选（7天内）
    if due_soon_only:
        today = date.today()
        week_later = today + timedelta(days=7)
        query = query.where(
            and_(Debt.due_date.between(today, week_later), Debt.is_settled == False)
        )

    # 按更新时间倒序排列
    query = query.order_by(Debt.updated_at.desc())

    # 分页查询
    def transform_debt(debt):
        return DebtResponse.from_orm_with_days(debt)

    return await paginate_response(
        db, query, pagination.page, pagination.size, transform_debt
    )


@router.post("/", response_model=DebtResponse)
async def create_debt(
    debt_data: DebtCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建债务记录"""
    debt = Debt(user_id=current_user.id, **debt_data.dict())

    db.add(debt)
    await db.commit()
    await db.refresh(debt)

    return DebtResponse.from_orm_with_days(debt)


@router.get("/summary", response_model=DebtSummary)
async def get_debt_summary(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """获取债务汇总统计"""
    # 获取汇总数据
    summary_query = select(
        func.coalesce(
            func.sum(case((Debt.type == DebtTypeEnum.BORROW_IN, Debt.amount), else_=0)),
            0,
        ).label("total_borrow_in"),
        func.coalesce(
            func.sum(case((Debt.type == DebtTypeEnum.LEND_OUT, Debt.amount), else_=0)),
            0,
        ).label("total_lend_out"),
        func.count(case((Debt.is_settled == True, 1), else_=None)).label(
            "settled_count"
        ),
        func.count(case((Debt.is_settled == False, 1), else_=None)).label(
            "unsettled_count"
        ),
        func.avg(Debt.amount).label("average_debt_amount"),
    ).where(Debt.user_id == current_user.id)

    result = await db.execute(summary_query)
    summary_data = result.first()

    # 计算逾期债务数量
    today = date.today()
    overdue_query = select(func.count()).where(
        and_(
            Debt.user_id == current_user.id,
            Debt.due_date < today,
            Debt.is_settled == False,
        )
    )
    overdue_result = await db.execute(overdue_query)
    overdue_count = overdue_result.scalar() or 0

    # 计算即将到期债务数量（7天内）
    week_later = today + timedelta(days=7)
    due_soon_query = select(func.count()).where(
        and_(
            Debt.user_id == current_user.id,
            Debt.due_date.between(today, week_later),
            Debt.is_settled == False,
        )
    )
    due_soon_result = await db.execute(due_soon_query)
    due_soon_count = due_soon_result.scalar() or 0

    total_borrow_in = summary_data.total_borrow_in or Decimal("0")
    total_lend_out = summary_data.total_lend_out or Decimal("0")
    net_amount = total_borrow_in - total_lend_out

    return DebtSummary(
        total_borrow_in=total_borrow_in,
        total_lend_out=total_lend_out,
        net_amount=net_amount,
        settled_count=summary_data.settled_count or 0,
        unsettled_count=summary_data.unsettled_count or 0,
        overdue_count=overdue_count,
        due_soon_count=due_soon_count,
        average_debt_amount=summary_data.average_debt_amount or Decimal("0"),
    )


@router.get("/{debt_id}", response_model=DebtResponse)
async def get_debt(
    debt_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取债务详情"""
    query = select(Debt).where(
        and_(Debt.id == debt_id, Debt.user_id == current_user.id)
    )
    result = await db.execute(query)
    debt = result.scalar_one_or_none()

    if not debt:
        raise HTTPException(status_code=404, detail="债务记录不存在")

    return DebtResponse.from_orm_with_days(debt)


@router.put("/{debt_id}", response_model=DebtResponse)
async def update_debt(
    debt_id: str,
    debt_data: DebtUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新债务记录"""
    query = select(Debt).where(
        and_(Debt.id == debt_id, Debt.user_id == current_user.id)
    )
    result = await db.execute(query)
    debt = result.scalar_one_or_none()

    if not debt:
        raise HTTPException(status_code=404, detail="债务记录不存在")

    # 更新字段
    update_data = debt_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(debt, field, value)

    await db.commit()
    await db.refresh(debt)

    return DebtResponse.from_orm_with_days(debt)


@router.patch("/{debt_id}/settle", response_model=DebtResponse)
async def settle_debt(
    debt_id: str,
    settle_data: DebtSettle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """结清债务"""
    query = select(Debt).where(
        and_(Debt.id == debt_id, Debt.user_id == current_user.id)
    )
    result = await db.execute(query)
    debt = result.scalar_one_or_none()

    if not debt:
        raise HTTPException(status_code=404, detail="债务记录不存在")

    debt.is_settled = settle_data.is_settled

    await db.commit()
    await db.refresh(debt)

    return DebtResponse.from_orm_with_days(debt)


@router.delete("/{debt_id}", response_model=MessageResponse)
async def delete_debt(
    debt_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除债务记录"""
    query = select(Debt).where(
        and_(Debt.id == debt_id, Debt.user_id == current_user.id)
    )
    result = await db.execute(query)
    debt = result.scalar_one_or_none()

    if not debt:
        raise HTTPException(status_code=404, detail="债务记录不存在")

    await db.delete(debt)
    await db.commit()

    return MessageResponse(message="债务记录已删除")
