"""
周期账单管理API
"""

from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...models.user import User
from ...models.recurring_bill import RecurringBill, FrequencyEnum
from ...models.bill import Bill
from ...models.asset import Asset
from ...models.category import Category
from ...schemas.recurring_bill import (
    RecurringBillCreate,
    RecurringBillUpdate,
    RecurringBillResponse,
    RecurringBillExecute,
    RecurringBillToggle,
    RecurringBillSummary,
)
from ...schemas.common import PaginatedResponse, MessageResponse
from ...utils.paginator import Paginator
from ...utils.pagination_params import PaginationParams
from ..deps import get_current_user
import uuid

router = APIRouter()


@router.get("", response_model=PaginatedResponse[RecurringBillResponse])
async def get_recurring_bills(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    frequency: Optional[FrequencyEnum] = Query(None, description="频率筛选"),
    due_soon: Optional[bool] = Query(None, description="是否即将到期(7天内)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取周期账单列表"""

    # 构建查询条件
    conditions = [RecurringBill.user_id == current_user.id]

    if is_active is not None:
        conditions.append(RecurringBill.is_active == is_active)

    if frequency is not None:
        conditions.append(RecurringBill.frequency == frequency)

    if due_soon:
        today = date.today()
        seven_days_later = today + timedelta(days=7)
        conditions.append(
            and_(
                RecurringBill.next_due_date <= seven_days_later,
                RecurringBill.next_due_date >= today,
            )
        )

    # 构建查询
    query = (
        select(RecurringBill)
        .where(and_(*conditions))
        .order_by(RecurringBill.next_due_date.asc())
    )

    # 转换函数
    def transform_recurring_bill(recurring_bill):
        data = {
            "id": str(recurring_bill.id),
            "user_id": str(recurring_bill.user_id),
            "template_bill_id": str(recurring_bill.template_bill_id),
            "name": recurring_bill.name,
            "amount": recurring_bill.amount,
            "currency": recurring_bill.currency,
            "asset_id": str(recurring_bill.asset_id),
            "category_id": str(recurring_bill.category_id),
            "frequency": recurring_bill.frequency,
            "next_due_date": recurring_bill.next_due_date,
            "end_date": recurring_bill.end_date,
            "is_active": recurring_bill.is_active,
            "description": recurring_bill.description,
            "created_at": recurring_bill.created_at,
            "updated_at": recurring_bill.updated_at,
        }
        return RecurringBillResponse(**data)

    # 使用分页器
    paginator = Paginator(db)
    params = PaginationParams(page=page, size=size)
    return await paginator.paginate_response(query, params, transform_recurring_bill)


@router.post("", response_model=RecurringBillResponse)
async def create_recurring_bill(
    recurring_bill_data: RecurringBillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建周期账单"""

    # 验证资产存在
    asset_query = select(Asset).where(
        and_(
            Asset.id == uuid.UUID(recurring_bill_data.asset_id),
            Asset.user_id == current_user.id,
        )
    )
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")

    # 验证分类存在
    category_query = select(Category).where(
        and_(
            Category.id == uuid.UUID(recurring_bill_data.category_id),
            Category.user_id == current_user.id,
        )
    )
    category_result = await db.execute(category_query)
    category = category_result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 创建模板账单ID (用于关联实际执行的账单)
    template_bill_id = uuid.uuid4()

    # 创建周期账单
    recurring_bill = RecurringBill(
        id=uuid.uuid4(),
        user_id=current_user.id,
        template_bill_id=template_bill_id,
        name=recurring_bill_data.name,
        amount=recurring_bill_data.amount,
        currency=recurring_bill_data.currency,
        asset_id=uuid.UUID(recurring_bill_data.asset_id),
        category_id=uuid.UUID(recurring_bill_data.category_id),
        frequency=recurring_bill_data.frequency,
        next_due_date=recurring_bill_data.next_due_date,
        end_date=recurring_bill_data.end_date,
        description=recurring_bill_data.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(recurring_bill)
    await db.commit()
    await db.refresh(recurring_bill)

    # 构建响应数据
    response_data = {
        "id": str(recurring_bill.id),
        "user_id": str(recurring_bill.user_id),
        "template_bill_id": str(recurring_bill.template_bill_id),
        "name": recurring_bill.name,
        "amount": recurring_bill.amount,
        "currency": recurring_bill.currency,
        "asset_id": str(recurring_bill.asset_id),
        "category_id": str(recurring_bill.category_id),
        "frequency": recurring_bill.frequency,
        "next_due_date": recurring_bill.next_due_date,
        "end_date": recurring_bill.end_date,
        "is_active": recurring_bill.is_active,
        "description": recurring_bill.description,
        "created_at": recurring_bill.created_at,
        "updated_at": recurring_bill.updated_at,
        "asset": {"id": str(asset.id), "name": asset.name, "type": asset.type},
        "category": {
            "id": str(category.id),
            "name": category.name,
            "icon": category.icon,
            "color": category.color,
        },
    }

    return RecurringBillResponse(**response_data)


@router.get("/{recurring_bill_id}", response_model=RecurringBillResponse)
async def get_recurring_bill(
    recurring_bill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取周期账单详情"""

    # 查询周期账单，包含关联信息
    query = select(RecurringBill).where(
        and_(
            RecurringBill.id == uuid.UUID(recurring_bill_id),
            RecurringBill.user_id == current_user.id,
        )
    )

    result = await db.execute(query)
    recurring_bill = result.scalar_one_or_none()

    if not recurring_bill:
        raise HTTPException(status_code=404, detail="周期账单不存在")

    # 获取关联的资产和分类信息
    asset_query = select(Asset).where(Asset.id == recurring_bill.asset_id)
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()

    category_query = select(Category).where(Category.id == recurring_bill.category_id)
    category_result = await db.execute(category_query)
    category = category_result.scalar_one_or_none()

    # 构建响应数据
    response_data = {
        "id": str(recurring_bill.id),
        "user_id": str(recurring_bill.user_id),
        "template_bill_id": str(recurring_bill.template_bill_id),
        "name": recurring_bill.name,
        "amount": recurring_bill.amount,
        "currency": recurring_bill.currency,
        "asset_id": str(recurring_bill.asset_id),
        "category_id": str(recurring_bill.category_id),
        "frequency": recurring_bill.frequency,
        "next_due_date": recurring_bill.next_due_date,
        "end_date": recurring_bill.end_date,
        "is_active": recurring_bill.is_active,
        "description": recurring_bill.description,
        "created_at": recurring_bill.created_at,
        "updated_at": recurring_bill.updated_at,
        "asset": {"id": str(asset.id), "name": asset.name, "type": asset.type}
        if asset
        else None,
        "category": {
            "id": str(category.id),
            "name": category.name,
            "icon": category.icon,
            "color": category.color,
        }
        if category
        else None,
    }

    return RecurringBillResponse(**response_data)


@router.put("/{recurring_bill_id}", response_model=RecurringBillResponse)
async def update_recurring_bill(
    recurring_bill_id: str,
    update_data: RecurringBillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新周期账单"""

    # 查询周期账单
    query = select(RecurringBill).where(
        and_(
            RecurringBill.id == uuid.UUID(recurring_bill_id),
            RecurringBill.user_id == current_user.id,
        )
    )

    result = await db.execute(query)
    recurring_bill = result.scalar_one_or_none()

    if not recurring_bill:
        raise HTTPException(status_code=404, detail="周期账单不存在")

    # 更新字段
    update_dict = update_data.model_dump(exclude_unset=True)

    # 验证资产和分类（如果有更新）
    if "asset_id" in update_dict:
        asset_query = select(Asset).where(
            and_(
                Asset.id == uuid.UUID(update_dict["asset_id"]),
                Asset.user_id == current_user.id,
            )
        )
        asset_result = await db.execute(asset_query)
        if not asset_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="资产不存在")
        update_dict["asset_id"] = uuid.UUID(update_dict["asset_id"])

    if "category_id" in update_dict:
        category_query = select(Category).where(
            and_(
                Category.id == uuid.UUID(update_dict["category_id"]),
                Category.user_id == current_user.id,
            )
        )
        category_result = await db.execute(category_query)
        if not category_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="分类不存在")
        update_dict["category_id"] = uuid.UUID(update_dict["category_id"])

    # 应用更新
    for field, value in update_dict.items():
        setattr(recurring_bill, field, value)

    recurring_bill.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(recurring_bill)

    # 获取关联信息
    asset_query = select(Asset).where(Asset.id == recurring_bill.asset_id)
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()

    category_query = select(Category).where(Category.id == recurring_bill.category_id)
    category_result = await db.execute(category_query)
    category = category_result.scalar_one_or_none()

    # 构建响应数据
    response_data = {
        "id": str(recurring_bill.id),
        "user_id": str(recurring_bill.user_id),
        "template_bill_id": str(recurring_bill.template_bill_id),
        "name": recurring_bill.name,
        "amount": recurring_bill.amount,
        "currency": recurring_bill.currency,
        "asset_id": str(recurring_bill.asset_id),
        "category_id": str(recurring_bill.category_id),
        "frequency": recurring_bill.frequency,
        "next_due_date": recurring_bill.next_due_date,
        "end_date": recurring_bill.end_date,
        "is_active": recurring_bill.is_active,
        "description": recurring_bill.description,
        "created_at": recurring_bill.created_at,
        "updated_at": recurring_bill.updated_at,
        "asset": {"id": str(asset.id), "name": asset.name, "type": asset.type}
        if asset
        else None,
        "category": {
            "id": str(category.id),
            "name": category.name,
            "icon": category.icon,
            "color": category.color,
        }
        if category
        else None,
    }

    return RecurringBillResponse(**response_data)


@router.delete("/{recurring_bill_id}", response_model=MessageResponse)
async def delete_recurring_bill(
    recurring_bill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除周期账单"""

    # 查询周期账单
    query = select(RecurringBill).where(
        and_(
            RecurringBill.id == uuid.UUID(recurring_bill_id),
            RecurringBill.user_id == current_user.id,
        )
    )

    result = await db.execute(query)
    recurring_bill = result.scalar_one_or_none()

    if not recurring_bill:
        raise HTTPException(status_code=404, detail="周期账单不存在")

    await db.delete(recurring_bill)
    await db.commit()

    return MessageResponse(
        success=True, message="周期账单删除成功", code=200, timestamp=datetime.utcnow()
    )


@router.post("/{recurring_bill_id}/execute", response_model=MessageResponse)
async def execute_recurring_bill(
    recurring_bill_id: str,
    execute_data: RecurringBillExecute,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """执行周期账单，创建实际账单记录"""

    # 查询周期账单
    query = select(RecurringBill).where(
        and_(
            RecurringBill.id == uuid.UUID(recurring_bill_id),
            RecurringBill.user_id == current_user.id,
            RecurringBill.is_active == True,
        )
    )

    result = await db.execute(query)
    recurring_bill = result.scalar_one_or_none()

    if not recurring_bill:
        raise HTTPException(status_code=404, detail="周期账单不存在或未激活")

    # 检查是否已经过了到期日期
    if (
        recurring_bill.end_date
        and execute_data.execution_date > recurring_bill.end_date
    ):
        raise HTTPException(status_code=400, detail="执行日期超过了周期账单结束日期")

    # 创建实际账单记录 (需要获取用户的默认账本)
    # 先获取用户的第一个账本作为默认账本
    from ...models.account import Account

    account_query = select(Account).where(Account.user_id == current_user.id).limit(1)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=400, detail="用户没有可用的账本")

    bill = Bill(
        id=uuid.uuid4(),
        user_id=current_user.id,
        account_id=account.id,  # 添加必需的账本ID
        amount=execute_data.amount or recurring_bill.amount,
        type="expense",  # 周期账单默认为支出
        currency=recurring_bill.currency,
        asset_id=recurring_bill.asset_id,
        category_id=recurring_bill.category_id,
        description=f"[周期账单] {recurring_bill.name}"
        + (f" - {execute_data.description}" if execute_data.description else ""),
        date=execute_data.execution_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(bill)

    # 更新下次到期日期
    next_due_date = _calculate_next_due_date(
        execute_data.execution_date, recurring_bill.frequency
    )
    recurring_bill.next_due_date = next_due_date
    recurring_bill.updated_at = datetime.utcnow()

    # 如果有结束日期且下次到期日期超过结束日期，则停用周期账单
    if recurring_bill.end_date and next_due_date > recurring_bill.end_date:
        recurring_bill.is_active = False

    await db.commit()

    return MessageResponse(
        success=True,
        message=f"周期账单执行成功，已创建金额为 {execute_data.amount or recurring_bill.amount} 的账单记录",
        code=200,
        timestamp=datetime.utcnow(),
    )


@router.patch("/{recurring_bill_id}/toggle", response_model=MessageResponse)
async def toggle_recurring_bill(
    recurring_bill_id: str,
    toggle_data: RecurringBillToggle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """切换周期账单的激活状态"""

    # 查询周期账单
    query = select(RecurringBill).where(
        and_(
            RecurringBill.id == uuid.UUID(recurring_bill_id),
            RecurringBill.user_id == current_user.id,
        )
    )

    result = await db.execute(query)
    recurring_bill = result.scalar_one_or_none()

    if not recurring_bill:
        raise HTTPException(status_code=404, detail="周期账单不存在")

    # 更新激活状态
    recurring_bill.is_active = toggle_data.is_active
    recurring_bill.updated_at = datetime.utcnow()

    await db.commit()

    status_text = "激活" if toggle_data.is_active else "停用"
    return MessageResponse(
        success=True,
        message=f"周期账单已{status_text}",
        code=200,
        timestamp=datetime.utcnow(),
    )


@router.get("/summary/statistics", response_model=RecurringBillSummary)
async def get_recurring_bills_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取周期账单统计汇总"""

    # 基础统计查询
    base_query = select(RecurringBill).where(RecurringBill.user_id == current_user.id)

    # 总数统计
    total_count_result = await db.execute(
        select(func.count(RecurringBill.id)).where(
            RecurringBill.user_id == current_user.id
        )
    )
    total_count = total_count_result.scalar() or 0

    # 激活状态统计
    active_count_result = await db.execute(
        select(func.count(RecurringBill.id)).where(
            and_(
                RecurringBill.user_id == current_user.id,
                RecurringBill.is_active == True,
            )
        )
    )
    active_count = active_count_result.scalar() or 0

    # 即将到期统计（7天内）
    today = date.today()
    seven_days_later = today + timedelta(days=7)
    due_soon_count_result = await db.execute(
        select(func.count(RecurringBill.id)).where(
            and_(
                RecurringBill.user_id == current_user.id,
                RecurringBill.is_active == True,
                RecurringBill.next_due_date <= seven_days_later,
                RecurringBill.next_due_date >= today,
            )
        )
    )
    due_soon_count = due_soon_count_result.scalar() or 0

    # 每月预估总支出
    monthly_estimated_result = await db.execute(
        select(func.sum(RecurringBill.amount)).where(
            and_(
                RecurringBill.user_id == current_user.id,
                RecurringBill.is_active == True,
            )
        )
    )
    monthly_estimated = monthly_estimated_result.scalar() or 0

    # 频率分布统计
    frequency_stats_result = await db.execute(
        select(
            RecurringBill.frequency,
            func.count(RecurringBill.id).label("count"),
            func.sum(RecurringBill.amount).label("total_amount"),
        )
        .where(
            and_(
                RecurringBill.user_id == current_user.id,
                RecurringBill.is_active == True,
            )
        )
        .group_by(RecurringBill.frequency)
    )

    frequency_distribution = {}
    for row in frequency_stats_result:
        frequency_distribution[row.frequency] = {
            "count": row.count,
            "total_amount": float(row.total_amount or 0),
        }

    return RecurringBillSummary(
        total_count=total_count,
        active_count=active_count,
        inactive_count=total_count - active_count,
        total_monthly_amount=float(monthly_estimated),
        due_soon_count=due_soon_count,
        overdue_count=0,  # 暂时设为0，可以后续实现逾期计算
        next_due_date=None,  # 可以后续添加下一个到期日期的计算
        frequency_distribution=frequency_distribution,
    )


def _calculate_next_due_date(current_date: date, frequency: FrequencyEnum) -> date:
    """计算下次到期日期"""
    if frequency == FrequencyEnum.DAILY:
        return current_date + timedelta(days=1)
    elif frequency == FrequencyEnum.WEEKLY:
        return current_date + timedelta(weeks=1)
    elif frequency == FrequencyEnum.MONTHLY:
        # 处理月份边界情况
        if current_date.month == 12:
            next_year = current_date.year + 1
            next_month = 1
        else:
            next_year = current_date.year
            next_month = current_date.month + 1

        # 处理月末日期问题（比如1月31日 -> 2月28/29日）
        try:
            return current_date.replace(year=next_year, month=next_month)
        except ValueError:
            # 如果日期不存在（如2月31日），则使用该月的最后一天
            from calendar import monthrange

            last_day = monthrange(next_year, next_month)[1]
            return current_date.replace(
                year=next_year, month=next_month, day=min(current_date.day, last_day)
            )
    elif frequency == FrequencyEnum.YEARLY:
        try:
            return current_date.replace(year=current_date.year + 1)
        except ValueError:
            # 处理闰年2月29日的情况
            return current_date.replace(year=current_date.year + 1, day=28)
    else:
        raise ValueError(f"不支持的频率类型: {frequency}")
