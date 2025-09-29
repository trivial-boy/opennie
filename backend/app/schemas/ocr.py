"""
OCR相关的数据模式
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class OCRLineResult(BaseModel):
    """OCR单行识别结果"""

    text: str = Field(..., description="识别的文字内容")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="置信度(0-1)")


class OCRResponse(BaseModel):
    """OCR识别响应"""

    success: bool = Field(..., description="是否识别成功")
    text: str = Field("", description="完整识别文本")
    lines: List[OCRLineResult] = Field(default_factory=list, description="逐行识别结果")
    line_count: int = Field(0, ge=0, description="识别的行数")
    error: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "success": True,
                "text": "滴滴出行\n-2.00\n先乘车后付款",
                "lines": [
                    {"text": "滴滴出行", "confidence": 0.998},
                    {"text": "-2.00", "confidence": 0.995},
                    {"text": "先乘车后付款", "confidence": 0.992},
                ],
                "line_count": 3,
                "error": None,
                "error_code": None,
            }
        }


class OCRSimpleResponse(BaseModel):
    """OCR简化响应（仅返回文本）"""

    text: str = Field("", description="识别的文本内容")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "text": "滴滴出行\n-2.00\n先乘车后付款\n当前状态 支付成功\n支付时间 2025年09月28日 21:32:41"
            }
        }
