from fastapi import APIRouter

from backend.database.manager import db_manager

router = APIRouter(
    prefix = "/api",
    tags = ["auth"],
    responses = {404: {"description": "Not found"}},
)

@router.post("/login")
def login(username: str, password: str):
    db_pwd = db_manager.get_administrator(username)
    if db_pwd and db_pwd == password:
        return {"status": "success"}
    else:
        return {"status": "error", "message": "Invalid credentials"}

@router.post("/change_login_password")
def change_password(username: str, old_password: str, new_password: str):
    db_pwd = db_manager.get_administrator(username)
    if db_pwd and db_pwd == old_password:
        db_manager.update_administrator_password(username, new_password)
        return {"status": "success"}
    else:
        return {"status": "error", "message": "Invalid credentials"}
