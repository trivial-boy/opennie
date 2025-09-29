"""
修复后的报表统计API
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ...core.database import get_db
from ...models.bill import Bill, TransactionTypeEnum
from ...models.user import User
from ...schemas.report import (
    IncomeExpenseSummaryResponse,
    ReportSummary,
    ReportGroup,
    ReportPeriodEnum,
    ReportPeriodInfo,
)
from ..deps import get_current_user

router = APIRouter()


@router.get("/income-expense-summary", response_model=IncomeExpenseSummaryResponse)
async def get_income_expense_summary(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    group_by: ReportPeriodEnum = Query(ReportPeriodEnum.MONTH, description="分组方式"),
    account_id: Optional[str] = Query(None, description="账本ID筛选"),
    category_ids: Optional[str] = Query(None, description="分类ID筛选(逗号分隔)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取收支汇总报表"""

    # 构建基础查询条件
    base_where = and_(
        Bill.user_id == current_user.id, Bill.date.between(start_date, end_date)
    )

    # 应用筛选条件
    conditions = [base_where]
    if account_id:
        conditions.append(Bill.account_id == account_id)
    if category_ids:
        category_id_list = category_ids.split(",")
        conditions.append(Bill.category_id.in_(category_id_list))

    final_where = and_(*conditions)

    # 获取收入总额
    income_query = select(func.coalesce(func.sum(Bill.amount), 0)).where(
        and_(final_where, Bill.type == TransactionTypeEnum.INCOME)
    )

    # 获取支出总额
    expense_query = select(func.coalesce(func.sum(Bill.amount), 0)).where(
        and_(final_where, Bill.type == TransactionTypeEnum.EXPENSE)
    )

    # 获取交易总数
    count_query = select(func.count()).where(final_where)

    # 执行查询
    income_result = await db.execute(income_query)
    expense_result = await db.execute(expense_query)
    count_result = await db.execute(count_query)

    total_income = income_result.scalar() or Decimal("0")
    total_expense = expense_result.scalar() or Decimal("0")
    transaction_count = count_result.scalar() or 0

    net_amount = total_income - total_expense

    return IncomeExpenseSummaryResponse(
        period=ReportPeriodInfo(
            start_date=start_date, end_date=end_date, group_by=group_by
        ),
        summary=ReportSummary(
            total_income=total_income,
            total_expense=total_expense,
            net_amount=net_amount,
            transaction_count=transaction_count,
        ),
        groups=[],  # 暂时不返回分组数据
    )


@router.get("/trend-analysis")
async def get_trend_analysis():
    """趋势分析 - 暂未实现"""
    return {"success": False, "message": "功能暂未实现"}


@router.get("/category-stats")
async def get_category_stats():
    """分类统计 - 暂未实现"""
    return {"success": False, "message": "功能暂未实现"}


@router.get("/comparison-analysis")
async def get_comparison_analysis():
    """对比分析 - 暂未实现"""
    return {"success": False, "message": "功能暂未实现"}
