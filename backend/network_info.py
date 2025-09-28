#!/usr/bin/env python3
"""
网络信息查看工具
"""

import subprocess
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


def get_local_ips():
    """获取本机所有网络接口的IP地址"""
    ips = []

    # 常见的网络接口名称
    interfaces = ["en0", "en1", "en2", "en3", "eth0", "wlan0"]

    for interface in interfaces:
        try:
            result = subprocess.run(
                ["ipconfig", "getifaddr", interface],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                ip = result.stdout.strip()
                if ip:
                    ips.append((interface, ip))
        except:
            continue

    return ips


def main():
    print("🌐 网络配置信息")
    print("=" * 50)

    # 获取配置信息
    print(f"📋 服务器配置:")
    print(f"   主机: {settings.SERVER_HOST}")
    print(f"   端口: {settings.SERVER_PORT}")
    print(f"   环境: {settings.ENVIRONMENT}")

    print(f"\n🔍 本机IP地址:")

    # 获取所有网络接口的IP
    ips = get_local_ips()

    if not ips:
        print("   ❌ 未找到有效的网络接口")
        return

    for interface, ip in ips:
        print(f"   {interface}: {ip}")

        # 检查是否为内网IP
        if ip.startswith(("192.168.", "10.", "172.")):
            print(f"      📱 局域网访问地址: http://{ip}:{settings.SERVER_PORT}")
            print(f"      📚 API文档地址: http://{ip}:{settings.SERVER_PORT}/docs")
            print(f"      🧪 健康检查: http://{ip}:{settings.SERVER_PORT}/health")

    print(f"\n💡 使用说明:")
    print(f"   1. 确保你的服务正在运行")
    print(f"   2. 其他设备连接到同一WiFi网络")
    print(f"   3. 使用上面的局域网地址访问服务")
    print(f"   4. 如果无法访问，检查防火墙设置")

    # 测试服务是否运行
    print(f"\n🔧 服务状态检查:")
    try:
        import requests

        response = requests.get(
            f"http://localhost:{settings.SERVER_PORT}/health", timeout=5
        )
        if response.status_code == 200:
            print(f"   ✅ 服务正常运行")
        else:
            print(f"   ⚠️ 服务响应异常: {response.status_code}")
    except ImportError:
        print(f"   ⚠️ 需要安装requests库进行检查")
    except Exception as e:
        print(f"   ❌ 服务未运行或无法访问: {str(e)}")


if __name__ == "__main__":
    main()
