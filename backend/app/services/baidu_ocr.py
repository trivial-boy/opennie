"""
百度OCR服务类
"""

import requests
import base64
import json
import os
import tempfile
from typing import List, Dict, Optional
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


class BaiduOCRService:
    """百度OCR服务类"""

    def __init__(self, api_key: str, secret_key: str):
        """
        初始化百度OCR客户端

        Args:
            api_key (str): 百度API Key
            secret_key (str): 百度Secret Key
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.access_token = None
        self.token_url = "https://aip.baidubce.com/oauth/2.0/token"
        self.ocr_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"

    def get_access_token(self) -> str:
        """获取百度API访问令牌"""
        if self.access_token:
            return self.access_token

        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }

        try:
            response = requests.post(
                self.token_url,
                params=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            self.access_token = result.get("access_token")

            if not self.access_token:
                raise ValueError(f"获取访问令牌失败: {result}")

            logger.info("成功获取百度OCR访问令牌")
            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"获取访问令牌网络请求错误: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"获取访问令牌解析错误: {e}")
            raise

    def image_bytes_to_base64(self, image_bytes: bytes) -> str:
        """将图片字节转换为base64编码"""
        try:
            base64_data = base64.b64encode(image_bytes).decode("utf-8")
            return base64_data
        except Exception as e:
            logger.error(f"图片base64编码错误: {e}")
            raise

    def recognize_text_from_bytes(self, image_bytes: bytes) -> Dict:
        """
        从图片字节识别文字

        Args:
            image_bytes (bytes): 图片字节数据

        Returns:
            Dict: 识别结果
        """
        try:
            # 获取访问令牌
            access_token = self.get_access_token()

            # 转换图片为base64
            base64_image = self.image_bytes_to_base64(image_bytes)

            # 准备请求参数
            params = {"access_token": access_token}

            payload = {
                "image": base64_image,
                "language_type": "CHN_ENG",  # 支持中英文混合
                "detect_direction": "true",  # 检测图像朝向
                "probability": "true",  # 返回识别结果中每一行的置信度
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            # 发送OCR请求
            response = requests.post(
                self.ocr_url,
                params=params,
                data=urlencode(payload),
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()

            # 检查是否有错误
            if "error_code" in result:
                error_msg = result.get("error_msg", "未知错误")
                logger.error(f"百度OCR识别错误: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": result.get("error_code"),
                    "text": "",
                    "lines": [],
                }

            # 提取文字内容
            words_result = result.get("words_result", [])
            recognized_lines = []
            full_text = ""

            for item in words_result:
                text = item.get("words", "")
                confidence = item.get("probability", {}).get("average", 0)
                recognized_lines.append(
                    {
                        "text": text,
                        "confidence": round(confidence, 3) if confidence else 0,
                    }
                )
                full_text += text + "\n"

            logger.info(f"成功识别文字，共 {len(recognized_lines)} 行")

            return {
                "success": True,
                "text": full_text.strip(),
                "lines": recognized_lines,
                "line_count": len(recognized_lines),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"OCR请求错误: {e}")
            return {
                "success": False,
                "error": f"网络请求错误: {str(e)}",
                "text": "",
                "lines": [],
            }
        except json.JSONDecodeError as e:
            logger.error(f"OCR响应解析错误: {e}")
            return {
                "success": False,
                "error": f"响应解析错误: {str(e)}",
                "text": "",
                "lines": [],
            }
        except Exception as e:
            logger.error(f"OCR处理错误: {e}")
            return {
                "success": False,
                "error": f"处理错误: {str(e)}",
                "text": "",
                "lines": [],
            }

    def recognize_text_from_file(self, file_path: str) -> Dict:
        """
        从图片文件识别文字

        Args:
            file_path (str): 图片文件路径

        Returns:
            Dict: 识别结果
        """
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            return self.recognize_text_from_bytes(image_bytes)
        except FileNotFoundError:
            logger.error(f"图片文件不存在: {file_path}")
            return {
                "success": False,
                "error": f"图片文件不存在: {file_path}",
                "text": "",
                "lines": [],
            }
        except Exception as e:
            logger.error(f"文件读取错误: {e}")
            return {
                "success": False,
                "error": f"文件读取错误: {str(e)}",
                "text": "",
                "lines": [],
            }


# 创建全局OCR服务实例
def create_ocr_service() -> Optional[BaiduOCRService]:
    """创建OCR服务实例"""
    api_key = os.getenv("BAIDU_OCR_API_KEY", "GXDbWbONIc6cjyIBrLQ6sZRQ")
    secret_key = os.getenv("BAIDU_OCR_SECRET_KEY", "AZIpImsP1oTSWw1UMmTpC3Sf4XBCCVvZ")

    if not api_key or not secret_key:
        logger.error("百度OCR API密钥未配置")
        return None

    return BaiduOCRService(api_key, secret_key)


# 全局OCR服务实例
ocr_service = create_ocr_service()
