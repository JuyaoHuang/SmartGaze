"""
Mock 模块 - 用于 PC 开发调试
提供模拟的摄像头和人脸引擎，避免硬件依赖
"""

import numpy as np
import cv2
from typing import Optional, List


class MockCamera:
    """模拟摄像头类 - 用于 PC 开发"""

    def __init__(self, index=0, mode=None):
        """初始化模拟摄像头"""
        print("[MockCamera] 开发模式：使用模拟摄像头")
        self.index = index
        self.mode = mode or "mock"
        self.actual_mode = "mock"
        self.width = 640
        self.height = 480
        self.fps = 30
        self.motion_contour_threshold = 500
        self._initialized = True

    def get_frame(self):
        """返回一个模拟的图像帧（纯色带文字）"""
        # 创建一个深灰色背景
        frame = np.ones((self.height, self.width, 3), dtype=np.uint8) * 50

        # 添加文字提示
        text = "Dev Mode - Mock Camera"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]

        # 计算文字位置（居中）
        text_x = (self.width - text_size[0]) // 2
        text_y = (self.height + text_size[1]) // 2

        # 绘制文字
        cv2.putText(
            frame,
            text,
            (text_x, text_y),
            font,
            font_scale,
            (255, 255, 255),
            font_thickness,
            cv2.LINE_AA,
        )

        # 添加时间戳
        import time

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame,
            timestamp,
            (20, self.height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )

        return frame

    def get_info(self):
        """返回摄像头信息"""
        return {
            "index": self.index,
            "mode": self.actual_mode,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "backend": "mock",
        }

    def detect_motion(self, prevFrame, frame, binary_threshold):
        """模拟移动检测（总是返回 False）"""
        return False

    def __del__(self):
        """析构函数"""
        print("[MockCamera] Mock camera released")


class MockFaceEngine:
    """模拟人脸引擎类 - 用于 PC 开发"""

    def __init__(self):
        """初始化模拟人脸引擎"""
        print("[MockFaceEngine] 开发模式：使用模拟人脸引擎")
        print("[MockFaceEngine] 注意：此模式不会进行真实的人脸识别")
        self._initialized = True

    def extract_feature(self, image_bytes: bytes) -> Optional[List[float]]:
        """
        模拟特征提取

        Args:
            image_bytes: JPEG 格式的图像字节数据

        Returns:
            模拟的 512 维特征向量（固定值）
        """
        # 返回一个固定的 512 维向量（用于测试）
        mock_feature = [0.1] * 512
        print(f"[MockFaceEngine] 模拟提取特征，长度: {len(mock_feature)}")
        return mock_feature

    def compare_features(self, feature1: List[float], feature2: List[float]) -> float:
        """
        模拟特征比对

        Args:
            feature1: 特征向量1
            feature2: 特征向量2

        Returns:
            相似度（0-1），模拟返回 0.95（高相似度）
        """
        # 模拟返回高相似度
        similarity = 0.95
        print(f"[MockFaceEngine] 模拟特征比对，相似度: {similarity}")
        return similarity

    def __del__(self):
        """析构函数"""
        print("[MockFaceEngine] Mock face engine destroyed")


# ========================================
# 全局单例实例（供 FastAPI 使用）
# ========================================

_mock_camera_instance: Optional[MockCamera] = None
_mock_face_engine_instance: Optional[MockFaceEngine] = None


def get_mock_camera() -> MockCamera:
    """获取全局 MockCamera 实例（单例模式）"""
    global _mock_camera_instance
    if _mock_camera_instance is None:
        _mock_camera_instance = MockCamera()
    return _mock_camera_instance


def get_mock_face_engine() -> MockFaceEngine:
    """获取全局 MockFaceEngine 实例（单例模式）"""
    global _mock_face_engine_instance
    if _mock_face_engine_instance is None:
        _mock_face_engine_instance = MockFaceEngine()
    return _mock_face_engine_instance
