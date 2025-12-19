from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.config import validate_config, print_config_summary, DEV_MODE
from backend.database.manager import db_manager as db
from backend.routers import auth, face, stream, unlock, pages

# 根据 DEV_MODE 选择导入真实模块或 Mock 模块
if DEV_MODE:
    print("[INFO] 开发模式：使用 Mock 模拟硬件")
    from backend.core.mock import get_mock_camera as get_camera
    from backend.core.mock import get_mock_face_engine as get_face_engine
    # 开发模式下不使用后台线程
    BackgroundThread = None
else:
    print("[INFO] 生产模式：加载真实硬件")
    from backend.core.camera import get_camera
    from backend.core.face_engine import get_face_engine
    from backend.core.backgroundThread import BackgroundThread


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时验证配置
    print("\n" + "="*60)
    print("智能门禁系统启动中...")
    print("="*60)

    # 验证配置
    is_valid = validate_config()
    if not is_valid:
        print("[ERROR] 配置验证失败，请检查 config.py")
        raise RuntimeError("配置验证失败")

    # 打印配置摘要
    print_config_summary()

    # 引擎初始化以及摄像头初始化
    print("正在初始化人脸识别引擎...")
    face_engine = get_face_engine()

    print("正在初始化摄像头...")
    camera = get_camera()

    # 仅在生产模式下启动后台守护线程
    back = None
    if not DEV_MODE and BackgroundThread:
        print("正在启动后台守护线程...")
        back = BackgroundThread()
        back.start()
    else:
        print("[INFO] 开发模式：跳过后台守护线程")

    print("\n[OK] 智能门禁系统启动成功！")
    if DEV_MODE:
        print("[提示] 当前为开发模式，使用 Mock 硬件模拟")
        print("[提示] 部署到 RK3568 前请将 config.py 中的 DEV_MODE 改为 False")
    print("="*60 + "\n")

    yield

    # 引擎销毁以及摄像头销毁
    print("\n智能门禁系统正在关闭...")
    if back:
        back.stop()
    db.close()  # 关闭数据库连接
    del face_engine
    del camera
    print("[OK] 系统已关闭\n")


app = FastAPI(lifespan=lifespan)

# 配置静态文件服务
STATIC_DIR = Path(__file__).resolve().parent.parent / "fronted" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 注册路由
app.include_router(pages.router)  # 页面路由（放在最前面，确保根路径正确处理）
app.include_router(auth.router)
app.include_router(face.router)
app.include_router(stream.router)
app.include_router(unlock.router)
