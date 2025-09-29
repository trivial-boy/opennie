#!/usr/bin/env python3
"""
百度OCR图片文字识别脚本

使用说明：
1. 需要先在百度AI开放平台申请OCR服务，获取API Key和Secret Key
2. 将图片文件路径作为参数传入
3. 脚本会输出识别到的文字内容

依赖库：requests, base64, json
如果缺少依赖，可以运行：pip install requests
"""

import requests
import base64
import json
import sys
import os
from urllib.parse import urlencode

class BaiduOCR:
    def __init__(self, api_key, secret_key):
        """
        初始化百度OCR客户端

        Args:
            api_key (str): 百度API Key
            secret_key (str): 百度Secret Key
        """
        self.api_key = GXDbWbONIc6cjyIBrLQ6sZRQ
        self.secret_key = AZIpImsP1oTSWw1UMmTpC3Sf4XBCCVvZ
        self.access_token = None
        self.token_url = "https://aip.baidubce.com/oauth/2.0/token"
        self.ocr_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"

    def get_access_token(self):
        """获取百度API访问令牌"""
        if self.access_token:
            return self.access_token

        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }

        try:
            response = requests.post(
                self.token_url,
                params=params,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()

            result = response.json()
            self.access_token = result.get('access_token')

            if not self.access_token:
                raise ValueError(f"获取访问令牌失败: {result}")

            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {e}")
            sys.exit(1)
        except (KeyError, ValueError) as e:
            print(f"API响应解析错误: {e}")
            sys.exit(1)

    def image_to_base64(self, image_path):
        """将图片转换为base64编码"""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                return base64_data
        except FileNotFoundError:
            print(f"图片文件未找到: {image_path}")
            sys.exit(1)
        except Exception as e:
            print(f"图片读取错误: {e}")
            sys.exit(1)

    def recognize_text(self, image_path):
        """
        识别图片中的文字

        Args:
            image_path (str): 图片文件路径

        Returns:
            list: 识别到的文字列表
        """
        if not os.path.exists(image_path):
            print(f"图片文件不存在: {image_path}")
            return []

        # 获取访问令牌
        access_token = self.get_access_token()

        # 转换图片为base64
        base64_image = self.image_to_base64(image_path)

        # 准备请求参数
        params = {
            "access_token": access_token
        }

        payload = {
            "image": base64_image,
            "language_type": "CHN_ENG",  # 支持中英文混合
            "detect_direction": "true",  # 检测图像朝向
            "probability": "true"  # 返回识别结果中每一行的置信度
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            # 发送OCR请求
            response = requests.post(
                self.ocr_url,
                params=params,
                data=urlencode(payload),
                headers=headers
            )
            response.raise_for_status()

            result = response.json()

            # 检查是否有错误
            if 'error_code' in result:
                print(f"OCR识别错误: {result.get('error_msg', '未知错误')}")
                return []

            # 提取文字内容
            words_result = result.get('words_result', [])
            recognized_text = []

            for item in words_result:
                text = item.get('words', '')
                confidence = item.get('probability', {}).get('average', 0)
                recognized_text.append({
                    'text': text,
                    'confidence': confidence
                })

            return recognized_text

        except requests.exceptions.RequestException as e:
            print(f"OCR请求错误: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"响应解析错误: {e}")
            return []

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python baidu_ocr.py <图片文件路径>")
        print("示例: python baidu_ocr.py image.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    # 这里需要替换为您的百度OCR API Key和Secret Key
    # 您可以从百度AI开放平台获取：https://ai.baidu.com/
    API_KEY = "your_api_key_here"
    SECRET_KEY = "your_secret_key_here"

    if API_KEY == "your_api_key_here" or SECRET_KEY == "your_secret_key_here":
        print("错误: 请设置您的百度OCR API Key和Secret Key")
        print("您可以在 https://ai.baidu.com/ 申请并获取这些密钥")
        print("\n修改脚本中的 API_KEY 和 SECRET_KEY 变量")
        sys.exit(1)

    # 创建OCR客户端
    ocr_client = BaiduOCR(API_KEY, SECRET_KEY)

    # 识别文字
    print(f"正在识别图片: {image_path}")
    results = ocr_client.recognize_text(image_path)

    if not results:
        print("未能识别到任何文字")
        return

    # 输出识别结果
    print(f"\n识别到 {len(results)} 行文字:")
    print("-" * 40)

    for i, result in enumerate(results, 1):
        text = result['text']
        confidence = result['confidence']
        print(f"{i:2d}. {text}")
        if confidence > 0:
            print(f"    置信度: {confidence:.2f}")

    print("-" * 40)
    print("识别完成!")

if __name__ == "__main__":
    main()
