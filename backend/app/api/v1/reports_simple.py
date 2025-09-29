"""
简化的报表统计API - 用于测试
"""

from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ...core.database import get_db
from ...models.bill import Bill
from ...models.user import User
from ...schemas.report import IncomeExpenseSummaryResponse, ReportSummary
from ..deps import get_current_user

router = APIRouter()


@router.get("/test-simple")
async def test_simple_query(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """简单测试查询"""

    # 最简单的查询
    query = select(func.count()).where(Bill.user_id == current_user.id)

    result = await db.execute(query)
    count = result.scalar()

    return {"success": True, "count": count, "message": "简单查询成功"}


@router.get("/test-summary")
async def test_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """测试基础统计查询"""

    # 简单的统计查询，不使用复杂的case语句
    query = select(func.count().label("total_count")).where(
        Bill.user_id == current_user.id
    )

    result = await db.execute(query)
    data = result.first()

    return {
        "success": True,
        "data": {
            "total_count": data.total_count if data else 0,
        },
        "message": "统计查询成功",
    }
