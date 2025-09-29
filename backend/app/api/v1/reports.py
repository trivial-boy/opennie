"""
报表统计API路由
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, desc, extract
from sqlalchemy.orm import joinedload

from ...core.database import get_db
from ...models.user import User
from ...models.bill import Bill, TransactionTypeEnum
from ...models.account import Account
from ...models.category import Category
from ...schemas.report import (
    IncomeExpenseSummaryResponse,
    TrendAnalysisResponse,
    CategoryStatsResponse,
    ComparisonAnalysisResponse,
    ReportQueryParams,
    TrendQueryParams,
    CategoryStatsQueryParams,
    ComparisonQueryParams,
    ReportPeriodEnum,
    ReportMetricEnum,
    ReportPeriodInfo,
    ReportSummary,
    ReportGroup,
    TrendDataPoint,
    TrendStatistics,
    CategoryStats,
    CategoryTrend,
    TopCategory,
    PeriodSummary,
    ComparisonSummary,
    CategoryComparison,
)
from ..deps import get_current_user

router = APIRouter()


def get_period_format(group_by: ReportPeriodEnum) -> str:
    """获取周期格式化字符串"""
    formats = {
        ReportPeriodEnum.DAY: "%Y-%m-%d",
        ReportPeriodEnum.WEEK: "%Y-W%U",
        ReportPeriodEnum.MONTH: "%Y-%m",
        ReportPeriodEnum.QUARTER: "%Y-Q%q",
        ReportPeriodEnum.YEAR: "%Y",
    }
    return formats.get(group_by, "%Y-%m")


def get_period_extract(group_by: ReportPeriodEnum):
    """获取周期提取表达式"""
    from sqlalchemy import text

    if group_by == ReportPeriodEnum.DAY:
        return func.date(Bill.date)
    elif group_by == ReportPeriodEnum.WEEK:
        return extract("week", Bill.date)
    elif group_by == ReportPeriodEnum.MONTH:
        return extract("month", Bill.date)
    elif group_by == ReportPeriodEnum.QUARTER:
        return extract("quarter", Bill.date)
    elif group_by == ReportPeriodEnum.YEAR:
        return extract("year", Bill.date)
    else:
        return func.date(Bill.date)


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

    # 构建基础查询
    query = select(Bill).where(
        and_(Bill.user_id == current_user.id, Bill.date.between(start_date, end_date))
    )

    # 应用筛选条件
    if account_id:
        query = query.where(Bill.account_id == account_id)

    if category_ids:
        category_id_list = category_ids.split(",")
        query = query.where(Bill.category_id.in_(category_id_list))

    # 获取汇总数据
    summary_query = select(
        func.coalesce(
            func.sum(
                case((Bill.type == TransactionTypeEnum.INCOME, Bill.amount), else_=0)
            ),
            0,
        ).label("total_income"),
        func.coalesce(
            func.sum(
                case((Bill.type == TransactionTypeEnum.EXPENSE, Bill.amount), else_=0)
            ),
            0,
        ).label("total_expense"),
        func.count().label("transaction_count"),
    )

    # Build WHERE conditions
    where_conditions = [
        Bill.user_id == current_user.id,
        Bill.date.between(start_date, end_date),
    ]

    if account_id:
        where_conditions.append(Bill.account_id == account_id)
    if category_ids:
        where_conditions.append(Bill.category_id.in_(category_ids.split(",")))

    summary_query = summary_query.where(and_(*where_conditions))

    summary_result = await db.execute(summary_query)
    summary_data = summary_result.first()

    total_income = summary_data.total_income or Decimal("0")
    total_expense = summary_data.total_expense or Decimal("0")
    net_amount = total_income - total_expense
    transaction_count = summary_data.transaction_count or 0

    # 获取分组数据
    period_expr = get_period_extract(group_by)

    group_query = (
        select(
            period_expr.label("period"),
            func.coalesce(
                func.sum(
                    case(
                        (Bill.type == TransactionTypeEnum.INCOME, Bill.amount), else_=0
                    )
                ),
                0,
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (Bill.type == TransactionTypeEnum.EXPENSE, Bill.amount), else_=0
                    )
                ),
                0,
            ).label("total_expense"),
            func.count().label("transaction_count"),
        )
        .where(and_(*where_conditions))
        .group_by(period_expr)
        .order_by(period_expr)
    )

    group_result = await db.execute(group_query)
    group_data = group_result.fetchall()

    # 构建响应数据
    groups = []
    for row in group_data:
        group_income = row.total_income or Decimal("0")
        group_expense = row.total_expense or Decimal("0")
        group_net = group_income - group_expense

        groups.append(
            ReportGroup(
                period=str(row.period),
                total_income=group_income,
                total_expense=group_expense,
                net_amount=group_net,
                transaction_count=row.transaction_count or 0,
            )
        )

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
        groups=groups,
    )


@router.get("/trend-analysis", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    metric: ReportMetricEnum = Query(..., description="分析指标"),
    period: str = Query("last_6_months", description="分析周期"),
    group_by: ReportPeriodEnum = Query(ReportPeriodEnum.MONTH, description="分组方式"),
    account_id: Optional[str] = Query(None, description="账本ID筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取趋势分析报表"""

    # 根据period参数计算日期范围
    today = date.today()
    if period == "last_6_months":
        start_date = today.replace(day=1) - timedelta(days=180)
        end_date = today
    elif period == "last_12_months":
        start_date = today.replace(day=1) - timedelta(days=365)
        end_date = today
    elif period == "current_year":
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif period == "last_year":
        last_year = today.year - 1
        start_date = date(last_year, 1, 1)
        end_date = date(last_year, 12, 31)
    else:
        # 默认最近6个月
        start_date = today.replace(day=1) - timedelta(days=180)
        end_date = today

    # 构建指标计算表达式
    if metric == ReportMetricEnum.INCOME:
        metric_expr = func.coalesce(
            func.sum(
                case((Bill.type == TransactionTypeEnum.INCOME, Bill.amount), else_=0)
            ),
            0,
        )
    elif metric == ReportMetricEnum.EXPENSE:
        metric_expr = func.coalesce(
            func.sum(
                case((Bill.type == TransactionTypeEnum.EXPENSE, Bill.amount), else_=0)
            ),
            0,
        )
    elif metric == ReportMetricEnum.NET_AMOUNT:
        metric_expr = func.coalesce(
            func.sum(
                case(
                    (Bill.type == TransactionTypeEnum.INCOME, Bill.amount),
                    else_=-Bill.amount,
                )
            ),
            0,
        )
    else:  # TRANSACTION_COUNT
        metric_expr = func.count()

    # 获取趋势数据
    period_expr = get_period_extract(group_by)

    trend_query = (
        select(period_expr.label("period"), metric_expr.label("value"))
        .where(
            and_(
                Bill.user_id == current_user.id,
                Bill.date.between(start_date, end_date),
                Bill.account_id == account_id if account_id else True,
            )
        )
        .group_by(period_expr)
        .order_by(period_expr)
    )

    trend_result = await db.execute(trend_query)
    trend_data = trend_result.fetchall()

    # 计算变化量和变化百分比
    data_points = []
    previous_value = None
    values = []

    for row in trend_data:
        value = row.value or Decimal("0")
        values.append(value)

        change = None
        change_percentage = None

        if previous_value is not None:
            change = value - previous_value
            if previous_value != 0:
                change_percentage = (change / previous_value) * 100
            else:
                change_percentage = Decimal("0")

        data_points.append(
            TrendDataPoint(
                period=str(row.period),
                value=value,
                change=change,
                change_percentage=change_percentage,
            )
        )

        previous_value = value

    # 计算统计信息
    if values:
        average = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        total_change = values[-1] - values[0] if len(values) > 1 else Decimal("0")
        total_change_percentage = (
            (total_change / values[0] * 100) if values[0] != 0 else Decimal("0")
        )
    else:
        average = min_value = max_value = total_change = total_change_percentage = (
            Decimal("0")
        )

    statistics = TrendStatistics(
        average=average,
        min=min_value,
        max=max_value,
        total_change=total_change,
        total_change_percentage=total_change_percentage,
    )

    return TrendAnalysisResponse(
        metric=metric,
        period=period,
        group_by=group_by,
        data_points=data_points,
        statistics=statistics,
    )


@router.get("/category-stats", response_model=CategoryStatsResponse)
async def get_category_stats(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    type: str = Query(..., description="统计类型(income/expense)"),
    account_id: Optional[str] = Query(None, description="账本ID筛选"),
    compare_with_previous: bool = Query(False, description="是否与上期对比"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分类统计报表"""

    # 确定交易类型
    if type == "income":
        transaction_type = TransactionTypeEnum.INCOME
    elif type == "expense":
        transaction_type = TransactionTypeEnum.EXPENSE
    else:
        raise HTTPException(status_code=400, detail="无效的统计类型")

    # 获取分类统计数据
    stats_query = (
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            Category.icon.label("category_icon"),
            Category.color.label("category_color"),
            func.coalesce(func.sum(Bill.amount), 0).label("amount"),
            func.count(Bill.id).label("transaction_count"),
            func.coalesce(func.avg(Bill.amount), 0).label("average_amount"),
        )
        .select_from(Bill)
        .join(Category, Bill.category_id == Category.id)
        .where(
            and_(
                Bill.user_id == current_user.id,
                Bill.type == transaction_type,
                Bill.date.between(start_date, end_date),
                Bill.account_id == account_id if account_id else True,
            )
        )
        .group_by(Category.id, Category.name, Category.icon, Category.color)
        .order_by(func.sum(Bill.amount).desc())
    )

    stats_result = await db.execute(stats_query)
    stats_data = stats_result.fetchall()

    # 计算总金额
    total_amount = sum(row.amount for row in stats_data)

    # 构建分类统计数据
    categories = []
    top_categories = []

    for i, row in enumerate(stats_data):
        amount = row.amount or Decimal("0")
        percentage = (amount / total_amount * 100) if total_amount > 0 else Decimal("0")

        # 如果需要对比上期数据
        trend = None
        if compare_with_previous:
            # 计算上期日期范围
            period_length = (end_date - start_date).days
            previous_start = start_date - timedelta(days=period_length)
            previous_end = start_date - timedelta(days=1)

            # 获取上期金额
            previous_query = select(func.coalesce(func.sum(Bill.amount), 0)).where(
                and_(
                    Bill.user_id == current_user.id,
                    Bill.type == transaction_type,
                    Bill.category_id == row.category_id,
                    Bill.date.between(previous_start, previous_end),
                    Bill.account_id == account_id if account_id else True,
                )
            )

            previous_result = await db.execute(previous_query)
            previous_amount = previous_result.scalar() or Decimal("0")

            change = amount - previous_amount
            change_percentage = (
                (change / previous_amount * 100)
                if previous_amount > 0
                else Decimal("0")
            )

            trend = CategoryTrend(
                previous_period_amount=previous_amount,
                change=change,
                change_percentage=change_percentage,
            )

        category_stat = CategoryStats(
            category_id=str(row.category_id),
            category_name=row.category_name,
            category_icon=row.category_icon,
            category_color=row.category_color,
            amount=amount,
            percentage=percentage,
            transaction_count=row.transaction_count or 0,
            average_amount=row.average_amount or Decimal("0"),
            trend=trend,
        )

        categories.append(category_stat)

        # 前5名作为热门分类
        if i < 5:
            top_categories.append(
                TopCategory(
                    rank=i + 1,
                    category_name=row.category_name,
                    amount=amount,
                    percentage=percentage,
                )
            )

    return CategoryStatsResponse(
        type=type,
        total_amount=total_amount,
        categories=categories,
        top_categories=top_categories,
    )


@router.get("/comparison-analysis", response_model=ComparisonAnalysisResponse)
async def get_comparison_analysis(
    period1_start: date = Query(..., description="周期1开始日期"),
    period1_end: date = Query(..., description="周期1结束日期"),
    period2_start: date = Query(..., description="周期2开始日期"),
    period2_end: date = Query(..., description="周期2结束日期"),
    account_id: Optional[str] = Query(None, description="账本ID筛选"),
    include_category_comparison: bool = Query(True, description="是否包含分类对比"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取对比分析报表"""

    # 构建查询条件
    def build_query(start_date: date, end_date: date):
        conditions = [
            Bill.user_id == current_user.id,
            Bill.date.between(start_date, end_date),
        ]
        if account_id:
            conditions.append(Bill.account_id == account_id)
        return and_(*conditions)

    # 获取两个周期的汇总数据
    async def get_period_summary(start_date: date, end_date: date) -> PeriodSummary:
        query = select(
            func.coalesce(
                func.sum(
                    case(
                        (Bill.type == TransactionTypeEnum.INCOME, Bill.amount), else_=0
                    )
                ),
                0,
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (Bill.type == TransactionTypeEnum.EXPENSE, Bill.amount), else_=0
                    )
                ),
                0,
            ).label("total_expense"),
        ).where(build_query(start_date, end_date))

        result = await db.execute(query)
        data = result.first()

        total_income = data.total_income or Decimal("0")
        total_expense = data.total_expense or Decimal("0")
        net_amount = total_income - total_expense

        return PeriodSummary(
            start_date=start_date,
            end_date=end_date,
            total_income=total_income,
            total_expense=total_expense,
            net_amount=net_amount,
        )

    period1 = await get_period_summary(period1_start, period1_end)
    period2 = await get_period_summary(period2_start, period2_end)

    # 计算对比数据
    income_change = period2.total_income - period1.total_income
    income_change_percentage = (
        (income_change / period1.total_income * 100)
        if period1.total_income > 0
        else Decimal("0")
    )

    expense_change = period2.total_expense - period1.total_expense
    expense_change_percentage = (
        (expense_change / period1.total_expense * 100)
        if period1.total_expense > 0
        else Decimal("0")
    )

    net_change = period2.net_amount - period1.net_amount
    net_change_percentage = (
        (net_change / period1.net_amount * 100)
        if period1.net_amount > 0
        else Decimal("0")
    )

    comparison = ComparisonSummary(
        income_change=income_change,
        income_change_percentage=income_change_percentage,
        expense_change=expense_change,
        expense_change_percentage=expense_change_percentage,
        net_change=net_change,
        net_change_percentage=net_change_percentage,
    )

    # 分类对比数据
    category_comparison = []
    if include_category_comparison:
        # 获取两个周期的分类数据
        async def get_category_amounts(
            start_date: date, end_date: date
        ) -> Dict[str, Decimal]:
            query = (
                select(
                    Category.name.label("category_name"),
                    func.coalesce(func.sum(Bill.amount), 0).label("amount"),
                )
                .select_from(Bill)
                .join(Category, Bill.category_id == Category.id)
                .where(build_query(start_date, end_date))
                .group_by(Category.name)
            )

            result = await db.execute(query)
            return {row.category_name: row.amount for row in result.fetchall()}

        period1_categories = await get_category_amounts(period1_start, period1_end)
        period2_categories = await get_category_amounts(period2_start, period2_end)

        # 合并所有分类名称
        all_categories = set(period1_categories.keys()) | set(period2_categories.keys())

        for category_name in all_categories:
            period1_amount = period1_categories.get(category_name, Decimal("0"))
            period2_amount = period2_categories.get(category_name, Decimal("0"))
            change = period2_amount - period1_amount
            change_percentage = (
                (change / period1_amount * 100) if period1_amount > 0 else Decimal("0")
            )

            category_comparison.append(
                CategoryComparison(
                    category_name=category_name,
                    period1_amount=period1_amount,
                    period2_amount=period2_amount,
                    change=change,
                    change_percentage=change_percentage,
                )
            )

        # 按变化金额排序
        category_comparison.sort(key=lambda x: abs(x.change), reverse=True)

    return ComparisonAnalysisResponse(
        period1=period1,
        period2=period2,
        comparison=comparison,
        category_comparison=category_comparison,
    )
