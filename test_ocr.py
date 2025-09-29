#!/usr/bin/env python3
"""
测试OCR接口脚本
"""

import requests
import os
import sys
from pathlib import Path


def test_ocr_api(image_path: str, api_url: str = "http://172.16.2.50:8000"):
    """测试OCR API接口"""

    # 检查图片文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        return False

    print(f"🔍 测试OCR接口...")
    print(f"📁 图片文件: {image_path}")
    print(f"🌐 API地址: {api_url}")
    print("-" * 50)

    # 测试详细版接口
    print("📋 测试详细版接口: /api/v1/ocr/recognize")
    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
            response = requests.post(
                f"{api_url}/api/v1/ocr/recognize", files=files, timeout=30
            )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                print("✅ 识别成功!")
                print(f"识别行数: {data.get('line_count', 0)}")
                print(f"完整文本:")
                print(data.get("text", ""))
                print("\n📋 逐行结果:")
                for i, line in enumerate(data.get("lines", []), 1):
                    print(
                        f"{i:2d}. {line.get('text', '')} (置信度: {line.get('confidence', 0):.3f})"
                    )
            else:
                print(f"❌ 识别失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 处理错误: {e}")
        return False

    print("\n" + "-" * 50)

    # 测试简化版接口（适用于dify）
    print("📝 测试简化版接口: /api/v1/ocr/recognize/simple")
    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
            response = requests.post(
                f"{api_url}/api/v1/ocr/recognize/simple", files=files, timeout=30
            )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                print("✅ 简化识别成功!")
                print("识别文本:")
                print(data.get("text", ""))
            else:
                print(f"❌ 简化识别失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ 简化请求失败: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 简化接口网络请求错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 简化接口处理错误: {e}")
        return False

    print("\n" + "-" * 50)

    # 测试健康检查
    print("🏥 测试健康检查: /api/v1/ocr/health")
    try:
        response = requests.get(f"{api_url}/api/v1/ocr/health", timeout=10)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ OCR服务健康!")
                data = result.get("data", {})
                print(f"服务状态: {data.get('status', '未知')}")
                print(f"服务类型: {data.get('service', '未知')}")
            else:
                print(f"⚠️ OCR服务异常: {result.get('message', '未知错误')}")
        else:
            print(f"❌ 健康检查失败: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 健康检查网络请求错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 健康检查处理错误: {e}")
        return False

    return True


def main():
    """主函数"""
    print("🚀 OCR接口测试工具")
    print("=" * 50)

    # 默认测试图片路径
    default_image = "test_image.jpg"

    # 检查命令行参数
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # 在当前目录查找图片文件
        image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        current_dir = Path(".")

        found_images = []
        for ext in image_extensions:
            found_images.extend(list(current_dir.glob(f"*{ext}")))
            found_images.extend(list(current_dir.glob(f"*{ext.upper()}")))

        if found_images:
            image_path = str(found_images[0])
            print(f"📷 自动发现图片文件: {image_path}")
        else:
            print("❌ 未找到测试图片文件")
            print("使用方法:")
            print("  python test_ocr.py <图片文件路径>")
            print("  python test_ocr.py test_image.jpg")
            print("\n或者将图片文件放在当前目录下")
            return

    # 检查API服务
    api_url = "http://172.16.2.50:8000"
    print(f"🔗 检查API服务: {api_url}")

    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API服务正常")
        else:
            print("⚠️ API服务异常，但继续测试OCR接口")
    except:
        print("⚠️ 无法连接API服务，请确保服务已启动")
        print("启动命令: ./restart-app.sh 或 docker-compose up -d")
        return

    print()

    # 执行OCR测试
    success = test_ocr_api(image_path, api_url)

    if success:
        print("\n🎉 OCR接口测试完成!")
        print("\n💡 dify调用示例:")
        print(f"POST {api_url}/api/v1/ocr/recognize/simple")
        print("Content-Type: multipart/form-data")
        print("Body: file=<image_file>")
    else:
        print("\n❌ OCR接口测试失败")
        print("\n🔧 故障排除:")
        print("1. 检查API服务是否正常运行")
        print("2. 检查百度OCR API密钥配置")
        print("3. 检查网络连接")
        print("4. 查看应用日志: ./dev-tools.sh logs")


if __name__ == "__main__":
    main()
