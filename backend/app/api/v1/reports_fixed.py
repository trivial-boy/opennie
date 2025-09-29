"""
修复后的报表统计API
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, extract, desc
from calendar import monthrange

from ...core.database import get_db
from ...models.bill import Bill, TransactionTypeEnum
from ...models.user import User
from ...models.category import Category
from ...schemas.report import (
    IncomeExpenseSummaryResponse,
    ReportSummary,
    ReportGroup,
    ReportPeriodEnum,
    ReportPeriodInfo,
    TrendAnalysisResponse,
    TrendDataPoint,
    TrendStatistics,
    ReportMetricEnum,
    CategoryStatsResponse,
    CategoryStats,
    CategoryTrend,
    TopCategory,
    ComparisonAnalysisResponse,
    PeriodSummary,
    ComparisonSummary,
    CategoryComparison,
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


@router.get("/trend-analysis", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    metric: ReportMetricEnum = Query(..., description="分析指标"),
    period: str = Query("last_6_months", description="分析周期"),
    group_by: ReportPeriodEnum = Query(ReportPeriodEnum.MONTH, description="分组方式"),
    account_id: Optional[str] = Query(None, description="账本ID筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """趋势分析"""

    # 解析周期参数，获取日期范围
    start_date, end_date = _parse_period(period)

    # 构建基础查询条件
    base_conditions = [
        Bill.user_id == current_user.id,
        Bill.date.between(start_date, end_date),
    ]

    if account_id:
        base_conditions.append(Bill.account_id == account_id)

    # 根据指标类型构建查询
    if metric == ReportMetricEnum.INCOME:
        base_conditions.append(Bill.type == TransactionTypeEnum.INCOME)
        value_expr = func.coalesce(func.sum(Bill.amount), 0)
    elif metric == ReportMetricEnum.EXPENSE:
        base_conditions.append(Bill.type == TransactionTypeEnum.EXPENSE)
        value_expr = func.coalesce(func.sum(Bill.amount), 0)
    elif metric == ReportMetricEnum.NET_AMOUNT:
        # 净收入 = 收入 - 支出
        income_expr = func.coalesce(
            func.sum(
                func.case(
                    (Bill.type == TransactionTypeEnum.INCOME, Bill.amount), else_=0
                )
            ),
            0,
        )
        expense_expr = func.coalesce(
            func.sum(
                func.case(
                    (Bill.type == TransactionTypeEnum.EXPENSE, Bill.amount), else_=0
                )
            ),
            0,
        )
        value_expr = income_expr - expense_expr
    else:  # TRANSACTION_COUNT
        value_expr = func.count(Bill.id)

    # 根据分组方式生成时间分组表达式
    if group_by == ReportPeriodEnum.DAY:
        time_group = Bill.date
        period_format = lambda d: d.strftime("%Y-%m-%d")
    elif group_by == ReportPeriodEnum.WEEK:
        time_group = func.date_trunc("week", Bill.date)
        period_format = lambda d: f"{d.strftime('%Y-%m-%d')} (Week)"
    elif group_by == ReportPeriodEnum.MONTH:
        time_group = func.date_trunc("month", Bill.date)
        period_format = lambda d: d.strftime("%Y-%m")
    elif group_by == ReportPeriodEnum.QUARTER:
        time_group = func.date_trunc("quarter", Bill.date)
        period_format = lambda d: f"{d.year}-Q{(d.month - 1) // 3 + 1}"
    else:  # YEAR
        time_group = func.date_trunc("year", Bill.date)
        period_format = lambda d: d.strftime("%Y")

    # 执行分组查询
    query = (
        select(time_group.label("period"), value_expr.label("value"))
        .where(and_(*base_conditions))
        .group_by(time_group)
        .order_by(time_group)
    )

    result = await db.execute(query)
    rows = result.fetchall()

    # 构建趋势数据点
    data_points = []
    previous_value = None

    for row in rows:
        period_date = row.period
        current_value = Decimal(str(row.value))

        # 计算变化量和百分比
        change = None
        change_percentage = None

        if previous_value is not None:
            change = current_value - previous_value
            if previous_value != 0:
                change_percentage = (change / previous_value) * 100
            else:
                change_percentage = Decimal("100") if change > 0 else Decimal("0")

        data_points.append(
            TrendDataPoint(
                period=period_format(period_date),
                value=current_value,
                change=change,
                change_percentage=change_percentage,
            )
        )

        previous_value = current_value

    # 计算统计信息
    if data_points:
        values = [dp.value for dp in data_points]
        average = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        total_change = data_points[-1].value - data_points[0].value
        total_change_percentage = (
            (total_change / data_points[0].value) * 100
            if data_points[0].value != 0
            else Decimal("0")
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
    """分类统计分析"""

    # 验证类型参数
    if type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="类型参数必须是 income 或 expense")

    transaction_type = (
        TransactionTypeEnum.INCOME if type == "income" else TransactionTypeEnum.EXPENSE
    )

    # 构建基础查询条件
    base_conditions = [
        Bill.user_id == current_user.id,
        Bill.date.between(start_date, end_date),
        Bill.type == transaction_type,
    ]

    if account_id:
        base_conditions.append(Bill.account_id == account_id)

    # 查询分类统计数据
    category_query = (
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            Category.icon.label("category_icon"),
            Category.color.label("category_color"),
            func.coalesce(func.sum(Bill.amount), 0).label("amount"),
            func.count(Bill.id).label("transaction_count"),
            func.coalesce(func.avg(Bill.amount), 0).label("average_amount"),
        )
        .select_from(
            Category.__table__.outerjoin(
                Bill.__table__, and_(Category.id == Bill.category_id, *base_conditions)
            )
        )
        .where(
            and_(Category.user_id == current_user.id, Category.type == transaction_type)
        )
        .group_by(Category.id, Category.name, Category.icon, Category.color)
        .having(func.sum(Bill.amount) > 0)  # 只显示有交易的分类
        .order_by(desc(func.sum(Bill.amount)))
    )

    result = await db.execute(category_query)
    rows = result.fetchall()

    # 计算总金额用于计算百分比
    total_amount = sum(Decimal(str(row.amount)) for row in rows)

    # 构建分类统计数据
    categories = []
    for row in rows:
        amount = Decimal(str(row.amount))
        percentage = (amount / total_amount * 100) if total_amount > 0 else Decimal("0")

        # 如果需要对比上一周期
        trend = None
        if compare_with_previous:
            # 计算上一周期的日期范围
            period_diff = end_date - start_date
            prev_start = start_date - period_diff
            prev_end = start_date

            # 查询上一周期的数据
            prev_conditions = [
                Bill.user_id == current_user.id,
                Bill.date.between(prev_start, prev_end),
                Bill.type == transaction_type,
                Bill.category_id == row.category_id,
            ]

            if account_id:
                prev_conditions.append(Bill.account_id == account_id)

            prev_query = select(func.coalesce(func.sum(Bill.amount), 0)).where(
                and_(*prev_conditions)
            )
            prev_result = await db.execute(prev_query)
            prev_amount = Decimal(str(prev_result.scalar() or 0))

            # 计算变化
            change = amount - prev_amount
            change_percentage = (
                (change / prev_amount * 100)
                if prev_amount > 0
                else (Decimal("100") if change > 0 else Decimal("0"))
            )

            trend = CategoryTrend(
                previous_period_amount=prev_amount,
                change=change,
                change_percentage=change_percentage,
            )

        categories.append(
            CategoryStats(
                category_id=str(row.category_id),
                category_name=row.category_name,
                category_icon=row.category_icon,
                category_color=row.category_color,
                amount=amount,
                percentage=percentage,
                transaction_count=row.transaction_count,
                average_amount=Decimal(str(row.average_amount)),
                trend=trend,
            )
        )

    # 构建TOP分类（前5名）
    top_categories = []
    for i, cat in enumerate(categories[:5]):
        top_categories.append(
            TopCategory(
                rank=i + 1,
                category_name=cat.category_name,
                amount=cat.amount,
                percentage=cat.percentage,
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
    """对比分析"""

    # 验证日期参数
    if period1_start > period1_end:
        raise HTTPException(status_code=400, detail="周期1开始日期不能大于结束日期")
    if period2_start > period2_end:
        raise HTTPException(status_code=400, detail="周期2开始日期不能大于结束日期")

    # 构建基础查询条件函数
    def build_period_conditions(start_date: date, end_date: date) -> list:
        conditions = [
            Bill.user_id == current_user.id,
            Bill.date.between(start_date, end_date),
        ]
        if account_id:
            conditions.append(Bill.account_id == account_id)
        return conditions

    # 获取周期1汇总数据
    period1_conditions = build_period_conditions(period1_start, period1_end)

    period1_income_query = select(func.coalesce(func.sum(Bill.amount), 0)).where(
        and_(*period1_conditions, Bill.type == TransactionTypeEnum.INCOME)
    )
    period1_expense_query = select(func.coalesce(func.sum(Bill.amount), 0)).where(
        and_(*period1_conditions, Bill.type == TransactionTypeEnum.EXPENSE)
    )

    period1_income_result = await db.execute(period1_income_query)
    period1_expense_result = await db.execute(period1_expense_query)

    period1_income = Decimal(str(period1_income_result.scalar() or 0))
    period1_expense = Decimal(str(period1_expense_result.scalar() or 0))
    period1_net = period1_income - period1_expense

    # 获取周期2汇总数据
    period2_conditions = build_period_conditions(period2_start, period2_end)

    period2_income_query = select(func.coalesce(func.sum(Bill.amount), 0)).where(
        and_(*period2_conditions, Bill.type == TransactionTypeEnum.INCOME)
    )
    period2_expense_query = select(func.coalesce(func.sum(Bill.amount), 0)).where(
        and_(*period2_conditions, Bill.type == TransactionTypeEnum.EXPENSE)
    )

    period2_income_result = await db.execute(period2_income_query)
    period2_expense_result = await db.execute(period2_expense_query)

    period2_income = Decimal(str(period2_income_result.scalar() or 0))
    period2_expense = Decimal(str(period2_expense_result.scalar() or 0))
    period2_net = period2_income - period2_expense

    # 计算变化量和百分比
    income_change = period2_income - period1_income
    income_change_percentage = (
        (income_change / period1_income * 100)
        if period1_income > 0
        else (Decimal("100") if income_change > 0 else Decimal("0"))
    )

    expense_change = period2_expense - period1_expense
    expense_change_percentage = (
        (expense_change / period1_expense * 100)
        if period1_expense > 0
        else (Decimal("100") if expense_change > 0 else Decimal("0"))
    )

    net_change = period2_net - period1_net
    net_change_percentage = (
        (net_change / period1_net * 100)
        if period1_net != 0
        else (
            Decimal("100")
            if net_change > 0
            else Decimal("-100")
            if net_change < 0
            else Decimal("0")
        )
    )

    # 构建周期汇总
    period1_summary = PeriodSummary(
        start_date=period1_start,
        end_date=period1_end,
        total_income=period1_income,
        total_expense=period1_expense,
        net_amount=period1_net,
    )

    period2_summary = PeriodSummary(
        start_date=period2_start,
        end_date=period2_end,
        total_income=period2_income,
        total_expense=period2_expense,
        net_amount=period2_net,
    )

    # 构建对比汇总
    comparison_summary = ComparisonSummary(
        income_change=income_change,
        income_change_percentage=income_change_percentage,
        expense_change=expense_change,
        expense_change_percentage=expense_change_percentage,
        net_change=net_change,
        net_change_percentage=net_change_percentage,
    )

    # 分类对比分析
    category_comparison = []
    if include_category_comparison:
        # 获取两个周期的分类统计
        category_query_base = (
            select(
                Category.name.label("category_name"),
                func.coalesce(func.sum(Bill.amount), 0).label("amount"),
            )
            .select_from(
                Category.__table__.outerjoin(
                    Bill.__table__, Category.id == Bill.category_id
                )
            )
            .where(Category.user_id == current_user.id)
            .group_by(Category.name)
        )

        # 周期1分类数据
        period1_category_query = category_query_base.where(
            and_(*period1_conditions) if period1_conditions else True
        )
        period1_category_result = await db.execute(period1_category_query)
        period1_categories = {
            row.category_name: Decimal(str(row.amount))
            for row in period1_category_result
        }

        # 周期2分类数据
        period2_category_query = category_query_base.where(
            and_(*period2_conditions) if period2_conditions else True
        )
        period2_category_result = await db.execute(period2_category_query)
        period2_categories = {
            row.category_name: Decimal(str(row.amount))
            for row in period2_category_result
        }

        # 合并所有分类并计算对比
        all_categories = set(period1_categories.keys()) | set(period2_categories.keys())

        for category_name in all_categories:
            period1_amount = period1_categories.get(category_name, Decimal("0"))
            period2_amount = period2_categories.get(category_name, Decimal("0"))

            # 只显示有变化的分类
            if period1_amount > 0 or period2_amount > 0:
                change = period2_amount - period1_amount
                change_percentage = (
                    (change / period1_amount * 100)
                    if period1_amount > 0
                    else (Decimal("100") if change > 0 else Decimal("0"))
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

        # 按变化量排序（绝对值）
        category_comparison.sort(key=lambda x: abs(x.change), reverse=True)

    return ComparisonAnalysisResponse(
        period1=period1_summary,
        period2=period2_summary,
        comparison=comparison_summary,
        category_comparison=category_comparison,
    )


def _parse_period(period: str) -> tuple[date, date]:
    """解析周期参数，返回开始和结束日期"""
    today = date.today()

    if period == "last_7_days":
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == "last_30_days":
        start_date = today - timedelta(days=30)
        end_date = today
    elif period == "last_3_months":
        start_date = today - timedelta(days=90)
        end_date = today
    elif period == "last_6_months":
        start_date = today - timedelta(days=180)
        end_date = today
    elif period == "last_12_months":
        start_date = today - timedelta(days=365)
        end_date = today
    elif period == "this_month":
        start_date = today.replace(day=1)
        _, last_day = monthrange(today.year, today.month)
        end_date = today.replace(day=last_day)
    elif period == "this_year":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        # 默认为最近6个月
        start_date = today - timedelta(days=180)
        end_date = today

    return start_date, end_date
