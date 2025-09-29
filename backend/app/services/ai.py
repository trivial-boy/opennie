"""
AI服务 - 集成Kimi大模型
"""

import json
import uuid
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from ..core.config import settings
from ..models.ai_conversation import AIConversation
from ..models.user import User
from ..schemas.ai import ChatResponse, AISuggestion
import logging

logger = logging.getLogger(__name__)


class AIService:
    """AI服务类 - 处理自然语言到SQL的转换和查询"""

    def __init__(self):
        self.kimi_api_url = settings.KIMI_API_URL
        self.kimi_api_key = settings.KIMI_API_KEY
        self.kimi_model = settings.KIMI_MODEL
        self.max_tokens = settings.KIMI_MAX_TOKENS
        self.temperature = settings.KIMI_TEMPERATURE

        # 数据库结构描述
        self.database_schema = self._get_database_schema()

    def _get_database_schema(self) -> str:
        """获取数据库结构描述"""
        return """
数据库结构说明：

1. 用户表 (users):
   - id: 用户ID (UUID)
   - username: 用户名
   - email: 邮箱
   - created_at: 创建时间

2. 账本表 (accounts):
   - id: 账本ID (UUID)
   - user_id: 用户ID (UUID)
   - name: 账本名称
   - description: 描述
   - currency: 货币类型
   - created_at: 创建时间

3. 资产表 (assets):
   - id: 资产ID (UUID)
   - user_id: 用户ID (UUID)
   - name: 资产名称
   - type: 资产类型 ('bank_account', 'credit_card', 'cash', 'investment', 'property', 'other')
   - balance: 余额 (DECIMAL)
   - currency: 货币
   - include_in_total: 是否计入总资产
   - created_at: 创建时间

4. 分类表 (categories):
   - id: 分类ID (UUID)
   - user_id: 用户ID (UUID)
   - name: 分类名称
   - type: 类型 ('income', 'expense', 'transfer')
   - icon: 图标
   - color: 颜色
   - parent_id: 父分类ID (UUID)
   - created_at: 创建时间

5. 账单表 (bills):
   - id: 账单ID (UUID)
   - user_id: 用户ID (UUID)
   - account_id: 账本ID (UUID)
   - asset_id: 资产ID (UUID)
   - category_id: 分类ID (UUID)
   - amount: 金额 (DECIMAL)
   - currency: 货币
   - type: 类型 ('income', 'expense', 'transfer')
   - description: 描述
   - date: 日期 (DATE)
   - created_at: 创建时间 (TIMESTAMP)

6. 债务表 (debts):
   - id: 债务ID (UUID)
   - user_id: 用户ID (UUID)
   - type: 类型 ('borrow_in', 'lend_out')
   - counterpart: 对方
   - amount: 金额 (DECIMAL)
   - description: 描述
   - due_date: 到期日期 (DATE)
   - is_settled: 是否已结清 (BOOLEAN)
   - created_at: 创建时间

7. 周期账单表 (recurring_bills):
   - id: 周期账单ID (UUID)
   - user_id: 用户ID (UUID)
   - name: 名称
   - amount: 金额 (DECIMAL)
   - asset_id: 资产ID (UUID)
   - category_id: 分类ID (UUID)
   - frequency: 频率 ('daily', 'weekly', 'monthly', 'yearly')
   - next_due_date: 下次执行日期 (DATE)
   - is_active: 是否激活 (BOOLEAN)
   - created_at: 创建时间

时间查询注意事项：
- 当前日期：使用 CURRENT_DATE
- 上周：使用 CURRENT_DATE - INTERVAL '1 week' 到 CURRENT_DATE - INTERVAL '1 day'
- 本周：使用 date_trunc('week', CURRENT_DATE) 到 CURRENT_DATE
- 本月：使用 date_trunc('month', CURRENT_DATE) 到 CURRENT_DATE
- 上月：使用 date_trunc('month', CURRENT_DATE - INTERVAL '1 month') 到 date_trunc('month', CURRENT_DATE) - INTERVAL '1 day'
"""

    async def generate_sql_prompt(self, user_message: str, user_id: str) -> str:
        """生成用于Kimi的SQL提示词"""
        prompt = f"""
你是一个专业的财务数据分析助手，能够将用户的自然语言查询转换为PostgreSQL查询语句。

数据库结构：
{self.database_schema}

用户ID: {user_id}

重要规则：
1. 所有查询必须包含 WHERE user_id = '{user_id}' 条件
2. 只能生成 SELECT 查询语句，不允许 INSERT、UPDATE、DELETE
3. 使用标准的PostgreSQL语法
4. 时间范围查询规则：
   - "上周": WHERE date >= CURRENT_DATE - INTERVAL '1 week' AND date < CURRENT_DATE
   - "本周": WHERE date >= date_trunc('week', CURRENT_DATE) AND date <= CURRENT_DATE
   - "本月": WHERE date >= date_trunc('month', CURRENT_DATE) AND date <= CURRENT_DATE
   - "上月": WHERE date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month') AND date < date_trunc('month', CURRENT_DATE)
   - "最近7天": WHERE date >= CURRENT_DATE - INTERVAL '7 days' AND date <= CURRENT_DATE
5. 对于支出查询，必须添加 AND type = 'expense'::transactiontypeenum 条件
6. 对于收入查询，必须添加 AND type = 'income'::transactiontypeenum 条件
7. 金额字段需要转换为数值：CAST(amount AS DECIMAL) 或直接使用 amount::DECIMAL
8. 使用 SUM、AVG、COUNT 等聚合函数进行统计
9. 需要分类信息时，使用 LEFT JOIN categories c ON b.category_id = c.id
10. 返回格式必须是JSON，包含sql字段和explanation字段

用户问题：{user_message}

请生成相应的SQL查询语句，并提供简单的解释。返回格式：
{{
  "sql": "SELECT ...",
  "explanation": "查询解释",
  "has_data_request": true/false
}}

如果用户问题不需要查询数据库（如问候、闲聊等），请设置has_data_request为false，并在explanation中提供友好的回复。
"""
        return prompt

    async def call_kimi_api(self, prompt: str) -> Dict[str, Any]:
        """调用Kimi API"""
        headers = {
            "Authorization": f"Bearer {self.kimi_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.kimi_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.kimi_api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Kimi API error: {response.status} - {error_text}"
                        )
                        raise Exception(f"Kimi API error: {response.status}")

        except asyncio.TimeoutError:
            logger.error("Kimi API timeout")
            raise Exception("AI服务响应超时")
        except Exception as e:
            logger.error(f"Kimi API call failed: {str(e)}")
            raise Exception(f"AI服务调用失败: {str(e)}")

    def parse_kimi_response(self, kimi_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析Kimi API响应"""
        try:
            content = kimi_response["choices"][0]["message"]["content"]
            # 尝试解析JSON内容
            if content.strip().startswith("{"):
                return json.loads(content)
            else:
                # 如果不是JSON，尝试提取SQL和解释
                return {"sql": None, "explanation": content, "has_data_request": False}
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse Kimi response: {str(e)}")
            return {
                "sql": None,
                "explanation": "抱歉，我无法理解您的问题，请重新描述。",
                "has_data_request": False,
            }

    async def execute_sql_query(self, sql: str, db: AsyncSession) -> Dict[str, Any]:
        """安全执行SQL查询"""
        try:
            # 安全检查：只允许SELECT语句
            sql_upper = sql.upper().strip()
            if not sql_upper.startswith("SELECT"):
                raise Exception("只允许执行SELECT查询")

            # 检查是否包含危险关键词 - 使用单词边界检查避免误报
            dangerous_keywords = [
                "DROP",
                "DELETE",
                "UPDATE",
                "INSERT",
                "ALTER",
                "CREATE",
                "TRUNCATE",
            ]
            import re

            for keyword in dangerous_keywords:
                # 使用正则表达式检查完整单词，避免字段名误报
                pattern = rf"\b{keyword}\b"
                if re.search(pattern, sql_upper):
                    raise Exception(f"查询包含不允许的关键词: {keyword}")

            # 修复枚举类型问题 - 将字符串值转换为正确的枚举转换语法
            # 修复枚举类型问题 - 转换为文本比较避免枚举错误
            sql = re.sub(
                r"type\s*=\s*'income'",
                r"type::text = 'income'",
                sql,
                flags=re.IGNORECASE,
            )
            sql = re.sub(
                r"type\s*=\s*'expense'",
                r"type::text = 'expense'",
                sql,
                flags=re.IGNORECASE,
            )
            sql = re.sub(
                r"type\s*=\s*'transfer'",
                r"type::text = 'transfer'",
                sql,
                flags=re.IGNORECASE,
            )

            logger.info(f"Executing SQL (after enum fix): {sql}")

            # 执行查询
            result = await db.execute(text(sql))
            rows = result.fetchall()

            # 获取列名
            columns = list(result.keys()) if rows else []

            # 转换结果为字典列表
            data = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # 处理特殊类型
                    if hasattr(value, "isoformat"):  # datetime
                        value = value.isoformat()
                    elif isinstance(value, uuid.UUID):
                        value = str(value)
                    elif hasattr(value, "__float__"):  # Decimal 类型
                        value = float(value)
                    row_dict[column] = value
                data.append(row_dict)

            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(data),
            }

        except Exception as e:
            logger.error(f"SQL execution error: {str(e)}")
            # 回滚事务以防止后续操作失败
            await db.rollback()
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "columns": [],
                "row_count": 0,
            }

    def format_query_result(
        self, query_result: Dict[str, Any], explanation: str
    ) -> str:
        """格式化查询结果为用户友好的文本"""
        if not query_result["success"]:
            return f"查询出现错误：{query_result['error']}"

        data = query_result["data"]
        row_count = query_result["row_count"]

        if row_count == 0:
            return f"{explanation}\n\n查询结果：没有找到相关数据。"

        # 构建结果文本
        result_text = f"{explanation}\n\n查询结果（共{row_count}条）：\n"

        # 简化显示逻辑，最多显示5条记录
        display_data = data[:5]
        for i, row in enumerate(display_data, 1):
            result_text += f"\n{i}. "
            row_items = []
            for key, value in row.items():
                if value is not None:
                    row_items.append(f"{key}: {value}")
            result_text += ", ".join(row_items)

        if row_count > 5:
            result_text += f"\n\n... 还有{row_count - 5}条记录"

        return result_text

    async def generate_suggestions(self) -> List[AISuggestion]:
        """生成AI建议"""
        suggestions = [
            AISuggestion(
                type="analysis",
                title="查看本月支出情况",
                description="分析本月的支出分布和趋势",
                priority=5,
                action="查询本月支出统计",
            ),
            AISuggestion(
                type="budget",
                title="设置预算目标",
                description="根据历史数据设置合理的预算目标",
                priority=4,
                action="创建预算计划",
            ),
            AISuggestion(
                type="saving",
                title="节省建议",
                description="基于支出分析提供节省建议",
                priority=3,
                action="查看节省建议",
            ),
        ]
        return suggestions

    async def chat(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[str],
        account_id: Optional[str],
        db: AsyncSession,
    ) -> ChatResponse:
        """处理AI对话"""
        try:
            # 生成或使用现有session_id
            if session_id is None:
                session_id = str(uuid.uuid4())
            else:
                session_id = str(session_id)

            # 生成SQL提示词
            prompt = await self.generate_sql_prompt(user_message, user_id)

            # 调用Kimi API
            kimi_response = await self.call_kimi_api(prompt)

            # 解析响应
            parsed_response = self.parse_kimi_response(kimi_response)

            sql_query = parsed_response.get("sql")
            explanation = parsed_response.get("explanation", "")
            has_data_request = parsed_response.get("has_data_request", False)

            query_result = None
            ai_response = explanation

            # 如果需要查询数据且有SQL语句
            if has_data_request and sql_query:
                query_result = await self.execute_sql_query(sql_query, db)
                ai_response = self.format_query_result(query_result, explanation)

            # 保存对话记录 - 确保query_result可以JSON序列化
            serializable_query_result = None
            if query_result:
                # 深度处理query_result，确保所有值都是JSON可序列化的
                serializable_query_result = json.loads(
                    json.dumps(query_result, default=str)
                )

            conversation = AIConversation(
                user_id=uuid.UUID(user_id),
                session_id=uuid.UUID(session_id),
                user_message=user_message,
                ai_response=ai_response,
                sql_query=sql_query,
                query_result=serializable_query_result,
            )
            db.add(conversation)
            await db.commit()

            # 生成建议的后续问题
            suggestions = [
                "查看我的总资产情况",
                "分析本月的收支情况",
                "显示最近的消费记录",
                "查看我的债务情况",
            ]

            return ChatResponse(
                session_id=uuid.UUID(session_id),
                response=ai_response,
                sql_query=sql_query,
                query_result=query_result,
                suggestions=suggestions,
            )

        except Exception as e:
            logger.error(f"AI chat error: {str(e)}")

            # 保存错误记录
            error_response = f"抱歉，处理您的请求时出现了错误：{str(e)}"
            conversation = AIConversation(
                user_id=uuid.UUID(user_id),
                session_id=uuid.UUID(session_id or str(uuid.uuid4())),
                user_message=user_message,
                ai_response=error_response,
                sql_query=None,
                query_result=None,
            )
            db.add(conversation)
            await db.commit()

            return ChatResponse(
                session_id=uuid.UUID(session_id or str(uuid.uuid4())),
                response=error_response,
                sql_query=None,
                query_result=None,
                suggestions=["请重新描述您的问题", "查看帮助文档"],
            )


# 创建全局AI服务实例
ai_service = AIService()
