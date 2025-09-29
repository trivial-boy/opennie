"""
AI对话API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional, List
from uuid import UUID
import uuid

from ...core.database import get_db
from ...schemas.ai import (
    ChatRequest,
    ChatResponse,
    AISuggestionsResponse,
    ConversationHistory,
)
from ...schemas.common import (
    ResponseModel,
    PaginatedResponse,
    PaginatedData,
    PaginationMeta,
)
from ...models.user import User
from ...models.ai_conversation import AIConversation
from ...api.deps import get_current_user
from ...services.ai import ai_service

router = APIRouter()


@router.post("/chat", response_model=ResponseModel[ChatResponse], summary="AI对话")
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    与AI进行对话，支持自然语言查询财务数据（无需认证）

    - **message**: 用户输入的消息
    - **session_id**: 会话ID（可选，为空时创建新会话）
    - **account_id**: 指定账本ID进行查询（可选）
    """
    try:
        response = await ai_service.chat(
            user_message=request.message,
            user_id=str(request.user_id),
            session_id=str(request.session_id) if request.session_id else None,
            account_id=str(request.account_id) if request.account_id else None,
            db=db,
        )

        return ResponseModel(data=response, message="AI对话成功")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI对话失败: {str(e)}",
        )


@router.get(
    "/suggestions",
    summary="获取AI建议",
)
async def get_ai_suggestions():
    """
    获取AI提供的财务建议（无需认证）
    """
    suggestions = [
        "查询我这个月的总收入和支出",
        "分析我的餐饮支出趋势",
        "查看我的资产分布情况",
        "比较这个月和上个月的支出差异",
        "查询我的信用卡账单明细",
        "统计我的资产总额",
        "查看最近一周的交易记录",
        "分析我的储蓄率变化",
        "查询我的投资收益情况",
        "比较不同分类的支出占比",
    ]

    return {"suggestions": suggestions}


@router.get(
    "/conversations",
    response_model=PaginatedResponse[ConversationHistory],
    summary="获取对话历史",
)
async def get_conversation_history(
    session_id: Optional[UUID] = Query(None, description="会话ID过滤"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户的AI对话历史记录

    - **session_id**: 会话ID过滤（可选）
    - **page**: 页码
    - **size**: 每页数量
    """
    try:
        # 构建查询条件
        conditions = [AIConversation.user_id == current_user.id]

        if session_id:
            conditions.append(AIConversation.session_id == session_id)

        # 计算偏移量
        offset = (page - 1) * size

        # 查询对话记录
        stmt = (
            select(AIConversation)
            .where(*conditions)
            .order_by(desc(AIConversation.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(stmt)
        conversations = result.scalars().all()

        # 查询总数
        count_stmt = select(func.count(AIConversation.id)).where(*conditions)
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

        # 转换为响应模型
        conversation_list = [
            ConversationHistory.model_validate(conv) for conv in conversations
        ]

        return PaginatedResponse(
            data=PaginatedData(
                items=conversation_list,
                pagination=pagination,
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话历史失败: {str(e)}",
        )


@router.get(
    "/sessions", response_model=ResponseModel[List[dict]], summary="获取会话列表"
)
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户的所有AI对话会话
    """
    try:
        # 查询不同的session_id及其最新对话时间
        stmt = (
            select(
                AIConversation.session_id,
                func.max(AIConversation.created_at).label("last_message_time"),
                func.count(AIConversation.id).label("message_count"),
                func.first_value(AIConversation.user_message)
                .over(
                    partition_by=AIConversation.session_id,
                    order_by=AIConversation.created_at.asc(),
                )
                .label("first_message"),
            )
            .where(AIConversation.user_id == current_user.id)
            .group_by(AIConversation.session_id)
            .order_by(desc(func.max(AIConversation.created_at)))
        )

        result = await db.execute(stmt)
        sessions = result.fetchall()

        session_list = []
        for session in sessions:
            session_list.append(
                {
                    "session_id": str(session.session_id),
                    "last_message_time": session.last_message_time.isoformat(),
                    "message_count": session.message_count,
                    "first_message": session.first_message[:50] + "..."
                    if len(session.first_message) > 50
                    else session.first_message,
                }
            )

        return ResponseModel(data=session_list, message="获取会话列表成功")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}",
        )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=ResponseModel[dict],
    summary="删除对话记录",
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除指定的对话记录
    """
    try:
        # 查找对话记录
        stmt = select(AIConversation).where(
            (AIConversation.id == conversation_id)
            & (AIConversation.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="对话记录不存在"
            )

        # 删除对话记录
        await db.delete(conversation)
        await db.commit()

        return ResponseModel(
            data={"id": str(conversation_id)}, message="删除对话记录成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除对话记录失败: {str(e)}",
        )


@router.delete(
    "/sessions/{session_id}", response_model=ResponseModel[dict], summary="删除整个会话"
)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除指定会话的所有对话记录
    """
    try:
        # 查找会话中的所有对话记录
        stmt = select(AIConversation).where(
            (AIConversation.session_id == session_id)
            & (AIConversation.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        conversations = result.scalars().all()

        if not conversations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        # 删除所有对话记录
        for conversation in conversations:
            await db.delete(conversation)

        await db.commit()

        return ResponseModel(
            data={"session_id": str(session_id), "deleted_count": len(conversations)},
            message="删除会话成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}",
        )
