#!/bin/bash
# 智能门禁系统启动脚本
# 此脚本用于系统开机自启动

set -e  # 遇到错误立即退出

# ========================================
# 配置项（根据实际情况修改）
# ========================================

# 项目路径（绝对路径）
PROJECT_DIR="/home/topeet/face_detection_system"

# Conda 环境名称
CONDA_ENV="rknn"

# Conda 安装路径（根据实际情况修改）
CONDA_PATH="/home/topeet/miniconda3"

# 日志目录
LOG_DIR="${PROJECT_DIR}/logs"

# ========================================
# 启动脚本
# ========================================

echo "=========================================="
echo "智能门禁系统启动脚本"
echo "=========================================="
echo "时间: $(date)"
echo "项目路径: ${PROJECT_DIR}"
echo "Conda环境: ${CONDA_ENV}"
echo ""

# 检查项目目录是否存在
if [ ! -d "${PROJECT_DIR}" ]; then
    echo "错误: 项目目录不存在: ${PROJECT_DIR}"
    exit 1
fi

# 进入项目目录
cd "${PROJECT_DIR}" || exit 1
echo "✓ 进入项目目录: $(pwd)"

# 创建日志目录
mkdir -p "${LOG_DIR}"
echo "✓ 日志目录: ${LOG_DIR}"

# 初始化 Conda
echo ""
echo "[1/4] 初始化 Conda..."
if [ -f "${CONDA_PATH}/etc/profile.d/conda.sh" ]; then
    source "${CONDA_PATH}/etc/profile.d/conda.sh"
    echo "✓ Conda 初始化成功"
else
    echo "错误: Conda 未找到，请检查路径: ${CONDA_PATH}"
    exit 1
fi

# 激活 Conda 环境
echo ""
echo "[2/4] 激活 Conda 环境: ${CONDA_ENV}..."
conda activate "${CONDA_ENV}"
if [ $? -eq 0 ]; then
    echo "✓ Conda 环境激活成功"
    echo "  Python 版本: $(python --version)"
else
    echo "错误: 无法激活 Conda 环境: ${CONDA_ENV}"
    exit 1
fi

# 等待网络就绪（可选，如果需要网络）
echo ""
echo "[3/4] 检查系统状态..."
sleep 5
echo "✓ 系统准备就绪"

# 启动后端服务
echo ""
echo "[4/4] 启动智能门禁系统..."
echo "=========================================="
echo ""

# 使用 nohup 在后台运行，并将输出重定向到日志文件
nohup python -m backend.main > "${LOG_DIR}/service.log" 2>&1 &

# 获取进程 ID
PID=$!
echo "✓ 服务已启动，PID: ${PID}"

# 保存 PID 到文件
echo ${PID} > "${PROJECT_DIR}/service.pid"

# 等待几秒，检查进程是否还在运行
sleep 3
if ps -p ${PID} > /dev/null; then
    echo "✓ 服务运行正常"
    echo ""
    echo "=========================================="
    echo "智能门禁系统启动成功！"
    echo "=========================================="
    echo "服务地址: http://$(hostname -I | awk '{print $1}'):8000"
    echo "日志文件: ${LOG_DIR}/service.log"
    echo "PID 文件: ${PROJECT_DIR}/service.pid"
    echo ""
    echo "查看日志: tail -f ${LOG_DIR}/service.log"
    echo "停止服务: kill $(cat ${PROJECT_DIR}/service.pid)"
    echo "=========================================="
else
    echo "✗ 服务启动失败"
    echo "请查看日志: ${LOG_DIR}/service.log"
    exit 1
fi
