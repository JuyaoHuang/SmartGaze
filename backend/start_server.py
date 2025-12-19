#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能门禁系统 - 后端服务启动脚本

使用方法：
    python backend/start_server.py
    或
    python -m backend.start_server

功能：
    - 启动 FastAPI 服务器
    - 自动读取配置文件
    - 提供启动信息
"""

import sys
import os
from pathlib import Path

# 设置默认编码为 UTF-8（解决 Windows 下的 GBK 编码问题）
if sys.platform == "win32":
    import locale

    # 设置标准输出为 UTF-8
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")
    # 设置文件系统编码
    os.environ["PYTHONIOENCODING"] = "utf-8"

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from backend.config import SERVER_HOST, SERVER_PORT, DEBUG_MODE, LOG_LEVEL


def print_startup_banner():
    """打印启动横幅"""
    print("\n" + "=" * 60)
    print("        智能门禁系统 - 后端服务")
    print("=" * 60)
    print(f"服务地址: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"调试模式: {'开启' if DEBUG_MODE else '关闭'}")
    print(f"日志级别: {LOG_LEVEL}")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务\n")


def check_dependencies():
    """检查必要的依赖是否安装"""
    # 包名映射：pip包名 -> 导入名
    package_mapping = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "jinja2": "jinja2",
        "opencv-python": "cv2",
        "PyJWT": "jwt",
        "python-multipart": "multipart",
    }

    missing_packages = []
    for pip_name, import_name in package_mapping.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)

    if missing_packages:
        print("[ERROR] 缺少必要的依赖包:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\n请运行: pip install -r requirements.txt")
        return False

    return True


def main():
    """主函数"""
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 打印启动信息
    print_startup_banner()

    # 启动 uvicorn 服务器
    try:
        uvicorn.run(
            "backend.main:app",
            host=SERVER_HOST,
            port=SERVER_PORT,
            reload=DEBUG_MODE,  # 调试模式下启用自动重载
            log_level=LOG_LEVEL.lower(),
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n\n[INFO] 服务已停止")
    except Exception as e:
        print(f"\n[ERROR] 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
