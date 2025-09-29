#!/bin/bash

# Docker镜像源速度测试脚本

set -e

echo "🏃‍♂️ 测试Docker镜像源下载速度..."

# 镜像源列表
declare -A MIRRORS=(
    ["Docker官方"]="docker.io"
    ["中科大镜像"]="docker.mirrors.ustc.edu.cn"
    ["网易镜像"]="hub-mirror.c.163.com"
    ["百度镜像"]="mirror.baidubce.com"
    ["阿里云镜像"]="registry.cn-hangzhou.aliyuncs.com"
    ["腾讯云镜像"]="ccr.ccs.tencentyun.com"
)

# 测试镜像
TEST_IMAGE="python:3.9.6-slim"

echo "📋 测试镜像: $TEST_IMAGE"
echo "🔍 测试镜像源数量: ${#MIRRORS[@]}"
echo ""

# 清理本地镜像缓存
echo "🧹 清理本地镜像缓存..."
docker rmi $TEST_IMAGE 2>/dev/null || true
docker system prune -f > /dev/null 2>&1

declare -A RESULTS=()

# 测试每个镜像源
for name in "${!MIRRORS[@]}"; do
    mirror=${MIRRORS[$name]}
    echo "⏱️ 测试 $name ($mirror)..."

    # 构建完整的镜像地址
    if [ "$mirror" == "docker.io" ]; then
        full_image="$TEST_IMAGE"
    else
        full_image="$mirror/library/$TEST_IMAGE"
    fi

    # 测试下载时间
    start_time=$(date +%s.%N)

    if timeout 120 docker pull $full_image > /dev/null 2>&1; then
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc -l)
        RESULTS[$name]=$duration
        printf "  ✅ 成功: %.2f秒\n" $duration
    else
        RESULTS[$name]="timeout"
        echo "  ❌ 失败: 超时或错误"
    fi

    # 清理下载的镜像
    docker rmi $full_image 2>/dev/null || true
    echo ""
done

echo "📊 测试结果汇总:"
echo "=================================="

# 排序结果
declare -A SORTED_RESULTS=()
for name in "${!RESULTS[@]}"; do
    result=${RESULTS[$name]}
    if [ "$result" != "timeout" ]; then
        SORTED_RESULTS[$name]=$result
    fi
done

# 显示成功的结果，按速度排序
if [ ${#SORTED_RESULTS[@]} -gt 0 ]; then
    echo "🏆 可用镜像源（按速度排序）:"
    for name in $(for k in "${!SORTED_RESULTS[@]}"; do echo "$k ${SORTED_RESULTS[$k]}"; done | sort -k2 -n | cut -d' ' -f1); do
        time=${SORTED_RESULTS[$name]}
        mirror=${MIRRORS[$name]}
        printf "  %d. %-12s %.2f秒 (%s)\n" $((++rank)) "$name" $time "$mirror"
    done

    # 推荐最快的镜像源
    fastest_name=$(for k in "${!SORTED_RESULTS[@]}"; do echo "$k ${SORTED_RESULTS[$k]}"; done | sort -k2 -n | head -1 | cut -d' ' -f1)
    fastest_mirror=${MIRRORS[$fastest_name]}
    fastest_time=${SORTED_RESULTS[$fastest_name]}

    echo ""
    echo "🚀 推荐使用: $fastest_name"
    echo "   镜像源: $fastest_mirror"
    printf "   速度: %.2f秒\n" $fastest_time

    # 提供配置建议
    echo ""
    echo "💡 配置建议:"
    echo "   sudo ./docker/setup-docker-mirrors.sh  # 配置镜像加速"
    echo "   docker-compose up --build              # 构建项目"
else
    echo "❌ 所有镜像源测试都失败了"
    echo "   请检查网络连接或Docker配置"
fi

echo ""
echo "📈 性能提升预期:"
if [ ${#SORTED_RESULTS[@]} -gt 0 ]; then
    echo "   相比官方源，最快的镜像源可提升 3-10倍 下载速度"
else
    echo "   配置镜像加速后，通常可提升 5-10倍 下载速度"
fi
echo ""
