from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from backend.database.manager import db_manager as db

# 配置模板路径
TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent / "fronted" / "templates"

# 创建 Jinja2 模板实例（显式指定 UTF-8 编码，解决 Windows 下的 GBK 编码问题）
templates = Jinja2Templates(directory=str(TEMPLATES_PATH))
# 配置 Jinja2 环境使用 UTF-8
templates.env.globals['encoding'] = 'utf-8'

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径 - 重定向到登录页面"""
    return RedirectResponse(url="/login")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "show_nav": False  # 登录页面不显示导航栏
    })


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """主控制面板"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request
    })


@router.get("/face_input", response_class=HTMLResponse)
async def face_input_page(request: Request):
    """人脸录入页面"""
    return templates.TemplateResponse("face_input.html", {
        "request": request
    })


@router.get("/face_dashboard", response_class=HTMLResponse)
async def face_dashboard_page(request: Request):
    """人脸管理面板"""
    return templates.TemplateResponse("face_dashboard.html", {
        "request": request
    })


@router.get("/face_list", response_class=HTMLResponse)
async def face_list_page(request: Request):
    """用户列表页面"""
    # 从数据库获取所有用户名列表
    names = db.get_face_name_list()

    # 格式化用户数据（由于数据库中没有创建时间，使用占位符）
    users_data = []
    for name in names:
        users_data.append({
            "username": name,
            "created_at": "未记录"  # 数据库中没有存储创建时间
        })

    return templates.TemplateResponse("face_list.html", {
        "request": request,
        "users": users_data
    })
