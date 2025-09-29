"""
报表统计相关的Pydantic模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ReportPeriodEnum(str, Enum):
    """报表统计周期枚举"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ReportMetricEnum(str, Enum):
    """报表指标枚举"""

    INCOME = "income"
    EXPENSE = "expense"
    NET_AMOUNT = "net_amount"
    TRANSACTION_COUNT = "transaction_count"


# 1. 收支汇总相关模型
class ReportPeriodInfo(BaseModel):
    """报表周期信息"""

    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    group_by: ReportPeriodEnum = Field(..., description="分组方式")


class ReportSummary(BaseModel):
    """报表汇总信息"""

    total_income: Decimal = Field(..., description="总收入")
    total_expense: Decimal = Field(..., description="总支出")
    net_amount: Decimal = Field(..., description="净收入")
    transaction_count: int = Field(..., description="交易笔数")


class ReportGroup(BaseModel):
    """报表分组数据"""

    period: str = Field(..., description="周期(如2024-01)")
    total_income: Decimal = Field(..., description="收入")
    total_expense: Decimal = Field(..., description="支出")
    net_amount: Decimal = Field(..., description="净收入")
    transaction_count: int = Field(..., description="交易笔数")


class IncomeExpenseSummaryResponse(BaseModel):
    """收支汇总响应"""

    period: ReportPeriodInfo = Field(..., description="统计周期")
    summary: ReportSummary = Field(..., description="汇总数据")
    groups: List[ReportGroup] = Field(..., description="分组数据")


# 2. 趋势分析相关模型
class TrendDataPoint(BaseModel):
    """趋势数据点"""

    period: str = Field(..., description="时间周期")
    value: Decimal = Field(..., description="数值")
    change: Optional[Decimal] = Field(None, description="变化量")
    change_percentage: Optional[Decimal] = Field(None, description="变化百分比")


class TrendStatistics(BaseModel):
    """趋势统计信息"""

    average: Decimal = Field(..., description="平均值")
    min: Decimal = Field(..., description="最小值")
    max: Decimal = Field(..., description="最大值")
    total_change: Decimal = Field(..., description="总变化量")
    total_change_percentage: Decimal = Field(..., description="总变化百分比")


class TrendAnalysisResponse(BaseModel):
    """趋势分析响应"""

    metric: ReportMetricEnum = Field(..., description="分析指标")
    period: str = Field(..., description="分析周期")
    group_by: ReportPeriodEnum = Field(..., description="分组方式")
    data_points: List[TrendDataPoint] = Field(..., description="趋势数据点")
    statistics: TrendStatistics = Field(..., description="统计信息")


# 3. 分类统计相关模型
class CategoryTrend(BaseModel):
    """分类趋势"""

    previous_period_amount: Decimal = Field(..., description="上期金额")
    change: Decimal = Field(..., description="变化量")
    change_percentage: Decimal = Field(..., description="变化百分比")


class CategoryStats(BaseModel):
    """分类统计"""

    category_id: str = Field(..., description="分类ID")
    category_name: str = Field(..., description="分类名称")
    category_icon: Optional[str] = Field(None, description="分类图标")
    category_color: Optional[str] = Field(None, description="分类颜色")
    amount: Decimal = Field(..., description="金额")
    percentage: Decimal = Field(..., description="占比百分比")
    transaction_count: int = Field(..., description="交易笔数")
    average_amount: Decimal = Field(..., description="平均交易金额")
    trend: Optional[CategoryTrend] = Field(None, description="趋势对比")


class TopCategory(BaseModel):
    """热门分类"""

    rank: int = Field(..., description="排名")
    category_name: str = Field(..., description="分类名称")
    amount: Decimal = Field(..., description="金额")
    percentage: Decimal = Field(..., description="占比百分比")


class CategoryStatsResponse(BaseModel):
    """分类统计响应"""

    type: str = Field(..., description="统计类型(income/expense)")
    total_amount: Decimal = Field(..., description="总金额")
    categories: List[CategoryStats] = Field(..., description="分类统计")
    top_categories: List[TopCategory] = Field(..., description="TOP分类")


# 4. 对比分析相关模型
class PeriodSummary(BaseModel):
    """周期汇总"""

    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    total_income: Decimal = Field(..., description="总收入")
    total_expense: Decimal = Field(..., description="总支出")
    net_amount: Decimal = Field(..., description="净收入")


class ComparisonSummary(BaseModel):
    """对比汇总"""

    income_change: Decimal = Field(..., description="收入变化")
    income_change_percentage: Decimal = Field(..., description="收入变化百分比")
    expense_change: Decimal = Field(..., description="支出变化")
    expense_change_percentage: Decimal = Field(..., description="支出变化百分比")
    net_change: Decimal = Field(..., description="净收入变化")
    net_change_percentage: Decimal = Field(..., description="净收入变化百分比")


class CategoryComparison(BaseModel):
    """分类对比"""

    category_name: str = Field(..., description="分类名称")
    period1_amount: Decimal = Field(..., description="周期1金额")
    period2_amount: Decimal = Field(..., description="周期2金额")
    change: Decimal = Field(..., description="变化量")
    change_percentage: Decimal = Field(..., description="变化百分比")


class ComparisonAnalysisResponse(BaseModel):
    """对比分析响应"""

    period1: PeriodSummary = Field(..., description="周期1汇总")
    period2: PeriodSummary = Field(..., description="周期2汇总")
    comparison: ComparisonSummary = Field(..., description="对比汇总")
    category_comparison: List[CategoryComparison] = Field(..., description="分类对比")


# 查询参数模型
class ReportQueryParams(BaseModel):
    """报表查询参数"""

    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    group_by: ReportPeriodEnum = Field(
        default=ReportPeriodEnum.MONTH, description="分组方式"
    )
    account_id: Optional[str] = Field(None, description="账本ID筛选")
    category_ids: Optional[List[str]] = Field(None, description="分类ID筛选")


class TrendQueryParams(BaseModel):
    """趋势分析查询参数"""

    metric: ReportMetricEnum = Field(..., description="分析指标")
    period: str = Field(..., description="分析周期(如last_6_months)")
    group_by: ReportPeriodEnum = Field(
        default=ReportPeriodEnum.MONTH, description="分组方式"
    )
    account_id: Optional[str] = Field(None, description="账本ID筛选")


class CategoryStatsQueryParams(BaseModel):
    """分类统计查询参数"""

    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    type: str = Field(..., description="统计类型(income/expense)")
    account_id: Optional[str] = Field(None, description="账本ID筛选")
    compare_with_previous: bool = Field(default=False, description="是否与上期对比")


class ComparisonQueryParams(BaseModel):
    """对比分析查询参数"""

    period1_start: date = Field(..., description="周期1开始日期")
    period1_end: date = Field(..., description="周期1结束日期")
    period2_start: date = Field(..., description="周期2开始日期")
    period2_end: date = Field(..., description="周期2结束日期")
    account_id: Optional[str] = Field(None, description="账本ID筛选")
    include_category_comparison: bool = Field(
        default=True, description="是否包含分类对比"
    )
