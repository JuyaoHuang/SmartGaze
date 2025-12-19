import logging
from typing import Optional

import cv2

from backend.config import (
    CAMERA_INDEX,
    CAMERA_MODE,
    GSTREAMER_PIPELINE,
    CAMERA_FALLBACK_INDICES,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
    MOTION_CONTOUR_THRESHOLD,
)


class Camera:
    """摄像头管理类 - 支持 GStreamer 和 OpenCV 双模切换"""

    def __init__(self, index=None, mode=None):
        """初始化函数，打开相机

        Args:
            index: 摄像头设备索引，None 则使用配置文件默认值
            mode: 初始化模式，None 则使用配置文件默认值
                  可选值: 'auto', 'gstreamer', 'opencv'
        """
        # 添加初始化标志，避免单例模式下重复初始化
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        # 使用配置文件中的默认值
        if index is None:
            index = CAMERA_INDEX
        if mode is None:
            mode = CAMERA_MODE

        self.index = index
        self.mode = mode
        self.cap = None
        self.actual_mode = None  # 记录实际使用的模式

        # 根据模式初始化摄像头
        if mode == "gstreamer":
            # 强制使用 GStreamer 模式
            logging.info(f"[Camera] 强制使用 GStreamer 模式")
            success = self._init_gstreamer(index)
            if not success:
                raise ValueError(f"Failed to open camera in GStreamer mode")

        elif mode == "opencv":
            # 强制使用 OpenCV 模式
            logging.info(f"[Camera] 强制使用 OpenCV 模式")
            success = self._init_opencv(index)
            if not success:
                raise ValueError(f"Failed to open camera in OpenCV mode")

        elif mode == "auto":
            # 自动模式：优先 GStreamer，失败则降级到 OpenCV
            logging.info(f"[Camera] 自动模式：优先尝试 GStreamer")
            success = self._init_gstreamer(index)

            if not success:
                logging.warning(f"[Camera] GStreamer 初始化失败，降级到 OpenCV 模式")
                success = self._init_opencv(index)

            if not success:
                raise ValueError(f"Failed to open camera in any mode")

        else:
            raise ValueError(
                f"Invalid camera mode: {mode}. Must be 'auto', 'gstreamer' or 'opencv'"
            )

        # 验证摄像头已成功打开
        if self.cap is None or not self.cap.isOpened():
            raise ValueError(f"Camera initialization failed")

        # 验证实际设置的分辨率
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        # 打印摄像头信息
        logging.info(f"[Camera] Camera opened successfully")
        logging.info(f"[Camera]   Mode:      {self.actual_mode}")
        logging.info(f"[Camera]   Device:    /dev/video{index}")
        logging.info(
            f"[Camera]   Requested: {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FPS}fps"
        )
        logging.info(
            f"[Camera]   Actual:    {actual_width}x{actual_height} @ {actual_fps}fps"
        )

        # 如果实际分辨率与请求不一致，发出警告
        if actual_width != CAMERA_WIDTH or actual_height != CAMERA_HEIGHT:
            logging.warning(
                f"[Camera] Resolution mismatch! "
                f"Requested {CAMERA_WIDTH}x{CAMERA_HEIGHT}, got {actual_width}x{actual_height}"
            )

        # 存储实际分辨率供后续使用
        self.width = actual_width
        self.height = actual_height
        self.fps = actual_fps

        # 初始化移动监测所需的变量
        self.motion_contour_threshold = MOTION_CONTOUR_THRESHOLD

    def _init_gstreamer(self, index):
        """使用 GStreamer 硬件加速管道初始化摄像头

        Args:
            index: 设备索引

        Returns:
            bool: 成功返回 True，失败返回 False
        """
        try:
            # 构建 GStreamer 管道字符串
            pipeline = GSTREAMER_PIPELINE.format(
                index=index, width=CAMERA_WIDTH, height=CAMERA_HEIGHT, fps=CAMERA_FPS
            )

            logging.info(f"[Camera] Trying GStreamer pipeline:")
            logging.info(f"[Camera]   {pipeline}")

            # 尝试打开 GStreamer 管道
            self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

            if not self.cap.isOpened():
                logging.warning(f"[Camera] GStreamer pipeline failed to open")
                return False

            # 尝试读取一帧验证
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logging.warning(f"[Camera] GStreamer opened but cannot read frames")
                self.cap.release()
                self.cap = None
                return False

            self.actual_mode = "gstreamer"
            logging.info(f"[Camera] GStreamer mode initialized successfully")
            return True

        except Exception as e:
            logging.warning(f"[Camera] GStreamer initialization exception: {e}")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            return False

    def _init_opencv(self, index):
        """使用标准 OpenCV V4L2 初始化摄像头

        Args:
            index: 设备索引（可以是单个索引或列表）

        Returns:
            bool: 成功返回 True，失败返回 False
        """
        # 如果指定了单个索引，只尝试该索引
        # 否则尝试配置文件中的所有索引
        if index is not None and index != CAMERA_INDEX:
            indices_to_try = [index]
        else:
            indices_to_try = CAMERA_FALLBACK_INDICES

        logging.info(f"[Camera] Trying OpenCV V4L2 mode with indices: {indices_to_try}")

        for idx in indices_to_try:
            try:
                logging.info(f"[Camera] Trying /dev/video{idx} ...")

                # 尝试打开设备
                self.cap = cv2.VideoCapture(idx)

                if not self.cap.isOpened():
                    logging.debug(f"[Camera]   /dev/video{idx} cannot open")
                    continue

                # 设置分辨率和帧率
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

                # 尝试读取一帧验证
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    logging.debug(f"[Camera]   /dev/video{idx} cannot read frames")
                    self.cap.release()
                    self.cap = None
                    continue

                # 成功
                self.index = idx  # 更新实际使用的索引
                self.actual_mode = "opencv"
                logging.info(
                    f"[Camera] OpenCV mode initialized successfully on /dev/video{idx}"
                )
                return True

            except Exception as e:
                logging.debug(f"[Camera]   /dev/video{idx} exception: {e}")
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                continue

        logging.warning(f"[Camera] OpenCV mode failed on all indices: {indices_to_try}")
        return False

    """析构函数，释放相机资源"""

    def __del__(self):
        self.cap.release()
        print(f"Camera{self.index} released")

    """获取一帧图像"""

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            logging.error("Failed to read frame from camera")
            return None
        return frame

    """获取摄像头信息"""

    def get_info(self):
        """返回摄像头的详细信息"""
        return {
            "index": self.index,
            "mode": self.actual_mode,  # 实际使用的模式
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "backend": self.cap.getBackendName()
            if hasattr(self.cap, "getBackendName")
            else "unknown",
        }

    """移动监测"""

    def detect_motion(self, prevFrame, frame, binary_threshold):
        # 转换为灰度图像
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 应用高斯模糊
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # 转换前一帧为灰度并模糊（如果不是灰度图像）
        if len(prevFrame.shape) > 2:
            prev_gray = cv2.cvtColor(prevFrame, cv2.COLOR_BGR2GRAY)
            prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
        else:
            prev_gray = prevFrame

        # 计算当前帧与前一帧的差异
        frame_delta = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(frame_delta, binary_threshold, 255, cv2.THRESH_BINARY)[1]

        # 扩展阈值图像，填充空洞
        thresh = cv2.dilate(thresh, None, iterations=2)

        # 查找轮廓
        contours, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # 如果轮廓面积超过阈值，认为检测到运动
        for contour in contours:
            if cv2.contourArea(contour) > self.motion_contour_threshold:
                return True

        return False


# ========================================
# 全局单例实例（供 FastAPI 使用）
# ========================================

# 延迟初始化：只在首次调用时创建实例
_camera_instance: Optional[Camera] = None


def get_camera() -> Camera:
    """
    获取全局 Camera 实例（单例模式）

    供 FastAPI 路由函数调用
    """
    global _camera_instance
    if _camera_instance is None:
        _camera_instance = Camera()
    return _camera_instance


if __name__ == "__main__":
    """单元测试：验证 Camera 功能"""
    import numpy as np

    print("=" * 60)
    print("开始测试 Camera")
    print("=" * 60)

    # 测试1: 单例模式
    print("\n[Test 1] 单例模式测试")
    try:
        cam1 = Camera()
        cam2 = Camera()
        if cam1 is cam2:
            print("[PASS] 单例模式正确：cam1 is cam2")
        else:
            print("[FAIL] 单例模式错误：创建了多个实例")
    except Exception as e:
        print(f"[INFO] 摄像头初始化失败（可能没有摄像头硬件）: {e}")
        print("[SKIP] 跳过后续需要硬件的测试")
        print("\n" + "=" * 60)
        print("测试完成（部分跳过）")
        print("=" * 60)
        exit(0)

    # 测试2: 初始化标志
    print("\n[Test 2] 初始化标志测试")
    try:
        cam = Camera()
        if hasattr(cam, "_initialized") and cam._initialized == True:
            print("[PASS] 初始化标志正确设置")
        else:
            print("[FAIL] 初始化标志未设置")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")

    # 测试3: 重复初始化
    print("\n[Test 3] 重复初始化测试（防止重复打开摄像头）")
    try:
        cam = Camera(index=0)
        original_cap = cam.cap
        # 再次调用 __init__（单例模式下会被调用）
        cam.__init__(index=0)
        if cam.cap is original_cap:
            print("[PASS] 重复初始化被正确阻止，摄像头未重新打开")
        else:
            print("[FAIL] 摄像头被重新打开")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")

    # 测试4: 获取帧
    print("\n[Test 4] 获取帧测试")
    try:
        cam = get_camera()
        frame = cam.get_frame()
        if frame is not None:
            print(f"[PASS] 成功获取帧，shape={frame.shape}")
        else:
            print("[FAIL] 获取帧失败")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")

    # 测试5: 运动检测算法（不需要真实运动）
    print("\n[Test 5] 运动检测算法测试")
    try:
        cam = get_camera()

        # 创建两个相同的测试帧（无运动）
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)

        motion_detected = cam.detect_motion(frame1, frame2, binary_threshold=25)

        if not motion_detected:
            print("[PASS] 相同帧检测无运动：正确")
        else:
            print("[FAIL] 相同帧检测到运动：错误")

        # 创建两个不同的帧（有运动）
        frame3 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame4 = np.ones((480, 640, 3), dtype=np.uint8) * 255

        motion_detected2 = cam.detect_motion(frame3, frame4, binary_threshold=25)

        if motion_detected2:
            print("[PASS] 完全不同的帧检测到运动：正确")
        else:
            print("[FAIL] 完全不同的帧未检测到运动：错误")

    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    # 测试6: 轮廓面积阈值设置
    print("\n[Test 6] 轮廓面积阈值测试")
    try:
        cam = get_camera()
        original_threshold = cam.motion_contour_threshold
        print(f"  默认轮廓面积阈值: {original_threshold}")

        # 修改阈值
        cam.motion_contour_threshold = 1000
        if cam.motion_contour_threshold == 1000:
            print("[PASS] 轮廓面积阈值可以修改")
        else:
            print("[FAIL] 轮廓面积阈值修改失败")

        # 恢复默认值
        cam.motion_contour_threshold = original_threshold
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")

    # 测试7: get_camera() 函数
    print("\n[Test 7] get_camera() 函数测试")
    try:
        cam1 = get_camera()
        cam2 = get_camera()
        if cam1 is cam2:
            print("[PASS] get_camera() 返回同一实例")
        else:
            print("[FAIL] get_camera() 返回不同实例")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n注意：如果没有摄像头硬件，某些测试会失败")
