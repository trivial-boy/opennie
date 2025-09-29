"""
AI相关Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from uuid import UUID
from datetime import datetime


class ChatRequest(BaseModel):
    """AI对话请求"""

    message: str = Field(
        ..., description="用户输入的消息", min_length=1, max_length=1000
    )
    user_id: UUID = Field(..., description="用户ID")
    session_id: Optional[UUID] = Field(None, description="会话ID，如果为空将创建新会话")
    account_id: Optional[UUID] = Field(None, description="指定账本ID进行查询")


class ChatResponse(BaseModel):
    """AI对话响应"""

    session_id: UUID = Field(..., description="会话ID")
    response: str = Field(..., description="AI回复内容")
    sql_query: Optional[str] = Field(None, description="生成的SQL查询语句")
    query_result: Optional[Dict[str, Any]] = Field(None, description="SQL查询结果")
    suggestions: Optional[List[str]] = Field(None, description="建议的后续问题")


class AISuggestion(BaseModel):
    """AI建议"""

    type: str = Field(..., description="建议类型：saving, budget, analysis, etc.")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议详细描述")
    priority: int = Field(..., description="优先级：1-5，数字越大优先级越高")
    action: Optional[str] = Field(None, description="建议的操作")


class AISuggestionsResponse(BaseModel):
    """AI建议响应"""

    suggestions: List[AISuggestion] = Field(..., description="建议列表")


class ConversationHistory(BaseModel):
    """对话历史"""

    id: UUID
    user_message: str
    ai_response: str
    sql_query: Optional[str]
    query_result: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
