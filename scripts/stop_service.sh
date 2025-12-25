#!/bin/bash
# 智能门禁系统停止脚本

set -e

# ========================================
# 配置项
# ========================================

PROJECT_DIR="/home/topeet/face_detection_system"
PID_FILE="${PROJECT_DIR}/service.pid"

# ========================================
# 停止脚本
# ========================================

echo "=========================================="
echo "停止智能门禁系统"
echo "=========================================="

# 检查 PID 文件是否存在
if [ ! -f "${PID_FILE}" ]; then
    echo "警告: PID 文件不存在: ${PID_FILE}"
    echo "尝试查找运行中的进程..."

    # 通过进程名查找
    PID=$(pgrep -f "python -m backend.main" || true)

    if [ -z "${PID}" ]; then
        echo "✓ 服务未运行"
        exit 0
    fi
else
    # 读取 PID
    PID=$(cat "${PID_FILE}")
fi

echo "找到进程 PID: ${PID}"

# 检查进程是否存在
if ps -p ${PID} > /dev/null 2>&1; then
    echo "正在停止服务..."

    # 发送 TERM 信号
    kill ${PID}

    # 等待进程结束（最多10秒）
    for i in {1..10}; do
        if ! ps -p ${PID} > /dev/null 2>&1; then
            echo "✓ 服务已停止"
            rm -f "${PID_FILE}"
            exit 0
        fi
        sleep 1
    done

    # 如果还没停止，强制终止
    echo "警告: 进程未响应，强制终止..."
    kill -9 ${PID}
    sleep 1

    if ! ps -p ${PID} > /dev/null 2>&1; then
        echo "✓ 服务已强制停止"
        rm -f "${PID_FILE}"
    else
        echo "✗ 无法停止服务"
        exit 1
    fi
else
    echo "✓ 服务未运行"
    rm -f "${PID_FILE}"
fi

echo "=========================================="
