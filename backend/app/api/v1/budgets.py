"""
预算API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from ...core.database import get_db
from ...schemas.budget import (
    BudgetCreate,
    BudgetRead,
    BudgetUpdate,
    BudgetWithCategories,
    BudgetCategoryRead,
    BudgetProgress,
)
from ...schemas.common import (
    ResponseModel,
    PaginatedResponse,
    PaginatedData,
    PaginationMeta,
)
from ...models.user import User
from ...models.budget import Budget, BudgetCategory, PeriodTypeEnum
from ...models.account import Account
from ...models.category import Category
from ...models.bill import Bill
from ...api.deps import get_current_user
import uuid

router = APIRouter()


@router.post("", response_model=ResponseModel[BudgetRead], summary="创建预算")
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新预算"""
    # 验证账本权限
    stmt = select(Account).where(
        (Account.id == budget_data.account_id) & (Account.user_id == current_user.id)
    )
    account = await db.execute(stmt)
    if not account.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="账本不存在或无权限"
        )

    # 验证分类权限
    if budget_data.categories:
        category_ids = [cat.category_id for cat in budget_data.categories]
        stmt = select(Category).where(
            (Category.id.in_(category_ids)) & (Category.user_id == current_user.id)
        )
        categories_result = await db.execute(stmt)
        existing_categories = categories_result.scalars().all()
        if len(existing_categories) != len(category_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="部分分类不存在或无权限"
            )

    # 创建预算
    budget_dict = budget_data.model_dump(exclude={"categories"})
    budget = Budget(user_id=current_user.id, **budget_dict)
    db.add(budget)
    await db.flush()

    # 创建预算分类明细
    if budget_data.categories:
        for cat_data in budget_data.categories:
            budget_category = BudgetCategory(
                budget_id=budget.id,
                category_id=cat_data.category_id,
                allocated_amount=cat_data.allocated_amount,
            )
            db.add(budget_category)

    await db.commit()
    await db.refresh(budget)

    return ResponseModel(data=BudgetRead.model_validate(budget), message="预算创建成功")


@router.get(
    "", response_model=PaginatedResponse[BudgetWithCategories], summary="获取预算列表"
)
async def get_budgets(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    account_id: Optional[uuid.UUID] = Query(None, description="账本ID"),
    period_type: Optional[PeriodTypeEnum] = Query(None, description="周期类型"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取预算列表"""
    # 构建查询条件
    conditions = [Budget.user_id == current_user.id]

    if account_id:
        conditions.append(Budget.account_id == account_id)
    if period_type:
        conditions.append(Budget.period_type == period_type)

    # 计算偏移量
    offset = (page - 1) * size

    # 查询预算列表
    stmt = (
        select(Budget)
        .where(and_(*conditions))
        .order_by(Budget.created_at.desc())
        .offset(offset)
        .limit(size)
    )

    result = await db.execute(stmt)
    budgets = result.scalars().all()

    # 查询总数
    count_stmt = select(func.count(Budget.id)).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 获取每个预算的详细信息
    budgets_with_details = []
    for budget in budgets:
        budget_detail = await _get_budget_with_categories(
            db, budget.id, current_user.id
        )
        budgets_with_details.append(budget_detail)

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
        data=PaginatedData(items=budgets_with_details, pagination=pagination)
    )


@router.get(
    "/{budget_id}",
    response_model=ResponseModel[BudgetWithCategories],
    summary="获取预算详情",
)
async def get_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取预算详情"""
    budget_detail = await _get_budget_with_categories(db, budget_id, current_user.id)
    if not budget_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预算不存在")

    return ResponseModel(data=budget_detail)


@router.put(
    "/{budget_id}", response_model=ResponseModel[BudgetRead], summary="更新预算"
)
async def update_budget(
    budget_id: uuid.UUID,
    budget_update: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新预算"""
    stmt = select(Budget).where(
        (Budget.id == budget_id) & (Budget.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预算不存在")

    # 更新预算
    update_data = budget_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    await db.commit()
    await db.refresh(budget)

    return ResponseModel(data=BudgetRead.model_validate(budget), message="预算更新成功")


@router.delete("/{budget_id}", response_model=ResponseModel[dict], summary="删除预算")
async def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除预算"""
    stmt = select(Budget).where(
        (Budget.id == budget_id) & (Budget.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预算不存在")

    # 删除预算分类明细
    delete_categories_stmt = select(BudgetCategory).where(
        BudgetCategory.budget_id == budget_id
    )
    categories_result = await db.execute(delete_categories_stmt)
    categories = categories_result.scalars().all()
    for category in categories:
        await db.delete(category)

    # 删除预算
    await db.delete(budget)
    await db.commit()

    return ResponseModel(data={"id": str(budget_id)}, message="预算删除成功")


@router.get(
    "/{budget_id}/progress",
    response_model=ResponseModel[BudgetProgress],
    summary="获取预算执行进度",
)
async def get_budget_progress(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取预算执行进度"""
    # 获取预算信息
    stmt = select(Budget).where(
        (Budget.id == budget_id) & (Budget.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预算不存在")

    # 获取预算详情
    budget_detail = await _get_budget_with_categories(db, budget_id, current_user.id)

    # 计算进度信息
    now = datetime.now().date()
    total_days = (budget.end_date - budget.start_date).days + 1
    days_elapsed = max(0, (now - budget.start_date).days + 1)
    days_remaining = max(0, (budget.end_date - now).days)

    daily_average_spent = (
        float(budget_detail.total_spent) / days_elapsed if days_elapsed > 0 else 0
    )
    projected_total = daily_average_spent * total_days

    progress = {
        "total_spent": budget_detail.total_spent,
        "remaining_amount": budget_detail.remaining_amount,
        "usage_percentage": budget_detail.usage_percentage,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "daily_average_spent": daily_average_spent,
        "projected_total": projected_total,
        "is_on_track": projected_total <= float(budget.total_amount),
    }

    # 生成预警信息
    alerts = []
    if budget_detail.usage_percentage > 90:
        alerts.append(
            {
                "type": "budget_exceeded",
                "category_name": "总预算",
                "message": f"预算已使用{budget_detail.usage_percentage:.1f}%，接近超支",
            }
        )

    for category in budget_detail.categories:
        if category.usage_percentage > 100:
            alerts.append(
                {
                    "type": "category_exceeded",
                    "category_name": category.category_name,
                    "message": f"分类'{category.category_name}'已超支{category.usage_percentage - 100:.1f}%",
                }
            )
        elif category.usage_percentage > 80:
            alerts.append(
                {
                    "type": "category_warning",
                    "category_name": category.category_name,
                    "message": f"分类'{category.category_name}'已使用{category.usage_percentage:.1f}%",
                }
            )

    budget_progress = BudgetProgress(
        budget=BudgetRead.model_validate(budget),
        progress=progress,
        categories=budget_detail.categories,
        alerts=alerts,
    )

    return ResponseModel(data=budget_progress)


async def _get_budget_with_categories(
    db: AsyncSession, budget_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[BudgetWithCategories]:
    """获取带分类的预算详情"""
    # 获取预算基础信息
    budget_stmt = select(Budget).where(
        (Budget.id == budget_id) & (Budget.user_id == user_id)
    )
    budget_result = await db.execute(budget_stmt)
    budget = budget_result.scalar_one_or_none()

    if not budget:
        return None

    # 获取预算分类明细
    categories_stmt = (
        select(BudgetCategory, Category.name.label("category_name"))
        .join(Category, BudgetCategory.category_id == Category.id)
        .where(BudgetCategory.budget_id == budget_id)
    )
    categories_result = await db.execute(categories_stmt)
    categories_data = categories_result.all()

    # 计算每个分类的已花费金额
    categories = []
    total_spent = Decimal("0.00")

    for budget_category, category_name in categories_data:
        # 查询该分类在预算期间的花费
        spent_stmt = select(func.coalesce(func.sum(Bill.amount), 0)).where(
            and_(
                Bill.user_id == user_id,
                Bill.account_id == budget.account_id,
                Bill.category_id == budget_category.category_id,
                Bill.type == "expense",
                Bill.date >= budget.start_date,
                Bill.date <= budget.end_date,
            )
        )
        spent_result = await db.execute(spent_stmt)
        spent_amount = spent_result.scalar() or Decimal("0.00")

        # 更新BudgetCategory的spent_amount
        budget_category.spent_amount = spent_amount

        remaining = budget_category.allocated_amount - spent_amount
        usage_percentage = (
            float(spent_amount / budget_category.allocated_amount * 100)
            if budget_category.allocated_amount > 0
            else 0
        )

        category_read = BudgetCategoryRead(
            id=budget_category.id,
            budget_id=budget_category.budget_id,
            category_id=budget_category.category_id,
            allocated_amount=budget_category.allocated_amount,
            spent_amount=spent_amount,
            category_name=category_name,
            remaining_amount=remaining,
            usage_percentage=usage_percentage,
        )
        categories.append(category_read)
        total_spent += spent_amount

    # 更新数据库中的spent_amount
    await db.commit()

    # 计算总体预算使用情况
    remaining_amount = budget.total_amount - total_spent
    usage_percentage = (
        float(total_spent / budget.total_amount * 100) if budget.total_amount > 0 else 0
    )

    budget_with_categories = BudgetWithCategories(
        id=budget.id,
        user_id=budget.user_id,
        account_id=budget.account_id,
        name=budget.name,
        total_amount=budget.total_amount,
        period_type=budget.period_type,
        start_date=budget.start_date,
        end_date=budget.end_date,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        categories=categories,
        total_spent=total_spent,
        remaining_amount=remaining_amount,
        usage_percentage=usage_percentage,
    )

    return budget_with_categories
