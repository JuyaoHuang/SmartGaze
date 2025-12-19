from fastapi import APIRouter
from pydantic import BaseModel

from backend.database.manager import db_manager
from backend.utils.auth import create_access_token
from backend.utils.password import verify_password

router = APIRouter(
    prefix="/api",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


# Pydantic 模型定义
class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    new_password: str


@router.post("/login")
async def login(request: LoginRequest):
    """管理员登录

    Args:
        request: 登录请求（JSON 格式）
            - username: 用户名
            - password: 明文密码

    Returns:
        成功返回 {"status": "success", "token": "<jwt_token>"}
        失败返回 {"status": "error", "msg": "Invalid credentials"}
    """
    # 从数据库获取 hash 后的密码
    hashed_password = db_manager.get_administrator(request.username)
    if hashed_password and verify_password(request.password, hashed_password):
        # 生成 JWT token
        token = create_access_token(request.username)
        return {"status": "success", "token": token}
    else:
        return {"status": "error", "msg": "账号或密码错误"}


@router.post("/change_login_password")
async def change_password(request: ChangePasswordRequest):
    """修改管理员密码

    Args:
        request: 修改密码请求（JSON 格式）
            - new_password: 新的明文密码

    Returns:
        成功返回 {"status": "success"}
        失败返回 {"status": "error", "msg": "..."}
    """
    # TODO: 从 Token 中获取当前用户名（需要添加认证依赖）
    # 暂时使用默认管理员用户名
    username = "admin"

    # 更新密码（数据库会自动 hash）
    try:
        db_manager.update_administrator_password(username, request.new_password)
        return {"status": "success", "msg": "密码修改成功"}
    except Exception as e:
        return {"status": "error", "msg": f"密码修改失败: {str(e)}"}
