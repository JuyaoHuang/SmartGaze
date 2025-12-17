from fastapi import APIRouter

from backend.core.camera import get_camera
from backend.core.face_engine import get_face_engine
from backend.database.manager import db_manager

router = APIRouter(
    prefix = "/api/face",
    tags = ["face"],
    responses = {404: {"description": "Not found"}},
)

@router.post("/capture")
async def capture_face(username: str):
    camera = get_camera()
    face_engine = get_face_engine()
    frame = camera.get_frame()
    if frame is None:
        return {"status": "error", "message": "Failed to capture frame"}
    # 录入人脸
    faces = face_engine.extract_feature(frame)
    if not faces:
        return {"status": "error", "message": "No face detected"}
    # 保存人脸特征向量
    if not db_manager.add_face_feature(username, faces):
        return {"status": "error", "message": "Failed to save face feature"}

    return {"status": "success"}

@router.get("/list")
async def getList():
    name_list = db_manager.get_face_name_list()
    return name_list

@router.delete("/{name}")
async def delete_face(name: str):
    if not db_manager.delete_face_name(name):
        return {"status": "error", "message": "Failed to delete face name"}
    return {"status": "success"}

@router.delete("/reset")
async def delete_all_faces():
    if not db_manager.delete_all_face_names():
        return {"status": "error", "message": "Failed to delete all face names"}
    return {"status": "success"}
