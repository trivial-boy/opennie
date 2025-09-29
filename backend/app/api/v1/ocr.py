"""
OCR图像文字识别API
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Union
import logging

from ...schemas.ocr import OCRResponse, OCRSimpleResponse
from ...schemas.common import ResponseModel
from ...services.baidu_ocr import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR图像识别"])


@router.post(
    "/recognize", response_model=ResponseModel[OCRResponse], summary="图像文字识别"
)
async def recognize_image(
    file: UploadFile = File(..., description="要识别的图像文件"),
):
    """
    识别图像中的文字内容

    支持的图像格式: JPG, JPEG, PNG, BMP, GIF
    文件大小限制: 最大4MB

    返回详细的识别结果，包括每行文字和置信度
    """
    # 检查OCR服务是否可用
    if not ocr_service:
        raise HTTPException(
            status_code=500, detail="OCR服务未配置，请检查百度API密钥设置"
        )

    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图像文件")

    # 验证文件大小 (4MB限制)
    max_size = 4 * 1024 * 1024  # 4MB

    try:
        # 读取文件内容
        file_content = await file.read()

        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="文件大小超过4MB限制")

        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="上传的文件为空")

        logger.info(
            f"开始OCR识别，文件名: {file.filename}, 大小: {len(file_content)} bytes"
        )

        # 调用OCR服务
        result = ocr_service.recognize_text_from_bytes(file_content)

        if result["success"]:
            logger.info(f"OCR识别成功，识别到 {result.get('line_count', 0)} 行文字")
            return ResponseModel(data=result, message="图像文字识别成功")
        else:
            logger.error(f"OCR识别失败: {result.get('error', '未知错误')}")
            raise HTTPException(
                status_code=500,
                detail=f"图像文字识别失败: {result.get('error', '未知错误')}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"OCR处理异常: {str(e)}")


@router.post(
    "/recognize/simple",
    response_model=ResponseModel[OCRSimpleResponse],
    summary="图像文字识别（简化版）",
)
async def recognize_image_simple(
    file: UploadFile = File(..., description="要识别的图像文件"),
):
    """
    识别图像中的文字内容（简化版）

    适用于dify等外部系统调用，仅返回识别的文本内容

    支持的图像格式: JPG, JPEG, PNG, BMP, GIF
    文件大小限制: 最大4MB
    """
    # 检查OCR服务是否可用
    if not ocr_service:
        raise HTTPException(status_code=500, detail="OCR服务未配置")

    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图像文件")

    try:
        # 读取文件内容
        file_content = await file.read()

        # 验证文件大小 (4MB限制)
        max_size = 4 * 1024 * 1024  # 4MB
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="文件大小超过4MB限制")

        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="上传的文件为空")

        logger.info(f"开始OCR简化识别，文件名: {file.filename}")

        # 调用OCR服务
        result = ocr_service.recognize_text_from_bytes(file_content)

        if result["success"]:
            return ResponseModel(
                data={"text": result.get("text", "")}, message="识别成功"
            )
        else:
            logger.error(f"OCR识别失败: {result.get('error', '未知错误')}")
            return ResponseModel(
                data={"text": ""},
                message=f"识别失败: {result.get('error', '未知错误')}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR简化处理异常: {e}")
        # 简化版接口即使出错也返回空文本，而不是抛出异常
        return ResponseModel(data={"text": ""}, message=f"处理异常: {str(e)}")


@router.get("/health", summary="OCR服务健康检查")
async def ocr_health_check():
    """检查OCR服务是否正常"""
    if not ocr_service:
        raise HTTPException(
            status_code=500, detail="OCR服务未配置: 百度OCR API密钥未设置"
        )

    try:
        # 尝试获取访问令牌来验证配置
        token = ocr_service.get_access_token()
        if token:
            return ResponseModel(
                data={"status": "healthy", "service": "baidu_ocr"},
                message="OCR服务正常",
            )
        else:
            raise HTTPException(
                status_code=500, detail="OCR服务配置错误: 无法获取访问令牌"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR服务异常: {str(e)}")
