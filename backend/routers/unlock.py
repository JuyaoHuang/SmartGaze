import threading
from fastapi import APIRouter, BackgroundTasks

from backend.core.doorController import get_door_controller
from backend.database.manager import db_manager

router = APIRouter(
    prefix="/api",
    tags=["unlock"],
    responses={404: {"description": "Not found"}},
)


@router.post("/unlock")
async def unlock(username: str, password: str, background_tasks: BackgroundTasks):
    """管理员远程开门

    Args:
        username: 管理员用户名
        password: 管理员密码
        background_tasks: FastAPI后台任务

    Returns:
        成功返回 {"status": "success"}，否则返回错误信息

    说明:
        - 验证管理员身份后，在后台线程中执行开门操作
        - 立即返回，不阻塞请求（开门操作需要3秒）
    """
    # 验证管理员身份
    db_pwd = db_manager.get_administrator(username)
    if not db_pwd or db_pwd != password:
        return {"status": "error", "message": "Invalid credentials"}

    # 在后台任务中执行开门操作
    def open_door():
        door_controller = get_door_controller()
        door_controller.open()

    background_tasks.add_task(open_door)

    return {"status": "success", "message": "Door unlock initiated"}
