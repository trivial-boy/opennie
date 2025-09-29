#!/usr/bin/env python3
"""
本地OCR测试脚本 - 直接使用百度OCR服务
"""

import sys
import os
from pathlib import Path

# 添加backend路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from app.services.baidu_ocr import BaiduOCRService
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


def create_test_image():
    """创建测试图片文件（基于你提供的图片内容）"""
    # 这里我们创建一个简单的测试图片描述文件
    test_content = """
    这是一个滴滴出行的支付截图，包含以下文字信息：

    滴滴出行
    等102万+人喜欢

    小程序        视频号
    更多优惠      前往视频号

    服务  优惠                    交易详情

    -2.00
    先乘车后付款

    当前状态    支付成功
    支付时间    2025年09月28日 21:32:41
    商品       先乘车后付款
    商户全称    杭州青奇科技有限公司
    收单机构    财付通支付科技有限公司
    支付方式    零钱
    交易单号    4200002842202509282050890889

    交易服务

    对订单有疑感          发起群收款
    在此商户的交易        管理扣费服务
    """

    print("📝 测试图片信息:")
    print(test_content)
    return None


def test_baidu_ocr_direct():
    """直接测试百度OCR服务"""
    print("🔍 直接测试百度OCR服务...")
    print("=" * 60)

    # 创建OCR服务实例
    api_key = "GXDbWbONIc6cjyIBrLQ6sZRQ"
    secret_key = "AZIpImsP1oTSWw1UMmTpC3Sf4XBCCVvZ"

    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"🔐 Secret Key: {secret_key[:10]}...")

    ocr_service = BaiduOCRService(api_key, secret_key)

    # 测试获取访问令牌
    print("\n🎫 测试获取访问令牌...")
    try:
        token = ocr_service.get_access_token()
        if token:
            print(f"✅ 成功获取访问令牌: {token[:20]}...")
        else:
            print("❌ 获取访问令牌失败")
            return False
    except Exception as e:
        print(f"❌ 获取访问令牌错误: {e}")
        return False

    print("\n📷 查找测试图片...")

    # 查找测试图片
    current_dir = Path(".")
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]

    found_images = []
    for ext in image_extensions:
        found_images.extend(list(current_dir.glob(f"*{ext}")))
        found_images.extend(list(current_dir.glob(f"*{ext.upper()}")))

    if not found_images:
        print("❌ 未找到测试图片文件")
        print("💡 请将测试图片文件放在当前目录下")
        print("支持格式: .jpg, .jpeg, .png, .bmp, .gif")
        return False

    # 使用第一个找到的图片
    test_image = str(found_images[0])
    print(f"📁 使用测试图片: {test_image}")

    # 进行OCR识别
    print(f"\n🔍 开始OCR识别...")
    try:
        result = ocr_service.recognize_text_from_file(test_image)

        print(f"📊 识别结果:")
        print("-" * 40)

        if result["success"]:
            print("✅ 识别成功!")
            print(f"📝 识别行数: {result.get('line_count', 0)}")
            print(f"\n📋 完整文本:")
            print(result.get("text", ""))

            print(f"\n📄 逐行结果:")
            lines = result.get("lines", [])
            for i, line in enumerate(lines, 1):
                text = line.get("text", "")
                confidence = line.get("confidence", 0)
                print(f"{i:2d}. {text}")
                if confidence > 0:
                    print(f"    置信度: {confidence:.3f}")

            print("-" * 40)
            print(f"🎉 OCR测试成功！识别到 {len(lines)} 行文字")
            return True
        else:
            print(f"❌ 识别失败: {result.get('error', '未知错误')}")
            error_code = result.get("error_code")
            if error_code:
                print(f"错误代码: {error_code}")
            return False

    except Exception as e:
        print(f"❌ OCR识别异常: {e}")
        return False


def main():
    """主函数"""
    print("🚀 本地OCR测试工具")
    print("=" * 60)

    # 检查依赖
    print("🔍 检查依赖...")
    try:
        import requests

        print("✅ requests库已安装")
    except ImportError:
        print("❌ 缺少requests库")
        print("安装命令: pip install requests")
        return

    # 显示测试图片信息
    create_test_image()

    # 执行OCR测试
    print("\n" + "=" * 60)
    success = test_baidu_ocr_direct()

    if success:
        print("\n🎉 本地OCR测试完成!")
        print("\n💡 接下来的步骤:")
        print("1. 确认OCR功能正常工作")
        print("2. 可以集成到FastAPI应用中")
        print("3. 供dify等外部系统调用")
    else:
        print("\n❌ 本地OCR测试失败")
        print("\n🔧 故障排除建议:")
        print("1. 检查百度OCR API密钥是否正确")
        print("2. 检查网络连接是否正常")
        print("3. 确认图片文件格式支持")
        print("4. 查看详细错误信息")


if __name__ == "__main__":
    main()
