## 数据库层 Database/manager.py 代码审查

1. 严重问题：SQL 参数传递错误 --- 已修复

    位置: backend/database/manager.py:52
    ```py
    self.cursor.execute('''
        SELECT id, username, password
        FROM administrators
        WHERE username = ?
    ''', username)  # ❌ 错误：应该是元组 (username,)
    ```
    问题说明: SQLite 的 execute 方法要求参数**必须是元组或列表，直接传字符串会导致错误**。

    同样的问题出现在:
    - backend/database/manager.py:87 delete_face_name 方法

    修复建议:
    ```python
    # 正确写法
    self.cursor.execute('... WHERE username = ?', (username,))
    self.cursor.execute('... WHERE name = ?', (name,))
    ```
---
1. 严重问题：类型不匹配 ---- 已修复

    位置: backend/database/manager.py:108
    ```py
    def add_face_feature(self, name: str, feature_vector: np.ndarray) -> bool:
        feature_blob = feature_vector.tobytes()  # ❌ 假设是 numpy 数组
    ```
    但是调用方传入的是 List[float]:

    位置: backend/routers/face.py:21-26
    ```py
    faces = face_engine.extract_feature(frame)  # 返回 List[float]
    if not db_manager.add_face_feature(username, faces):  # ❌ 传入 List，但期望 np.ndarray
    ```
    修复建议:
    ```py
    def add_face_feature(self, name: str, feature_vector) -> bool:
        # 统一转换为 numpy 数组
        if isinstance(feature_vector, list):
            feature_vector = np.array(feature_vector, dtype=np.float32)
        feature_blob = feature_vector.tobytes()
        # ...
    ```
---
1. 严重问题：线程安全问题 ---- 已修复

    位置: backend/database/manager.py:11
    ```py
    self.conn = sqlite3.connect(db_path)
    ```
    问题说明:
    - SQLite 连接默认不是线程安全的
    - 后台线程（BackgroundThread）和 FastAPI 请求会并发访问数据库
    - 可能导致 "database is locked" 错误

    修复建议:
    ```py
    self.conn = sqlite3.connect(db_path, check_same_thread=False)
    # 或者使用连接池
    ```
---
1. 设计问题：数据库路径相对路径 ---- 标注: 不需要改变，数据库确认位于 database/ 下

    位置: backend/database/manager.py:9, 148
    ```py
    def __init__(self, db_path: str = 'sm_door.db'):  # ❌ 相对路径
        self.conn = sqlite3.connect(db_path)

    db_manager = DatabaseManager()  # 使用默认相对路径
    ```
    问题说明:

    - 相对路径会根据运行时的工作目录变化
    - 可能导致在不同目录下创建多个数据库文件
    - 文档要求数据库应该在 backend 目录下

    修复建议:
    ```py
    from pathlib import Path

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 确保数据库在 backend 目录下
            backend_dir = Path(__file__).parent.parent
            db_path = str(backend_dir / "sm_door.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
    ```
---
1. 逻辑问题：delete_all_face_names 返回值错误 ---- 已修复

    位置: backend/database/manager.py:100
    ```py
    def delete_all_face_names(self) -> bool:
        try:
            self.cursor.execute('DELETE FROM face_features')
            self.conn.commit()
            return self.cursor.rowcount > 0  # ❌ 如果表为空，删除0行也应该返回True
    ```
    问题说明:
    - 删除全部操作即使表为空（删除0行）也应该算成功
    - 当前实现在表为空时返回 False

    修复建议:
    ```py
    return True  # 删除操作成功即返回 True
    ```
---
1. 缺失功能：没有关闭数据库连接的机制 

    位置: backend/database/manager.py:148
    ```py
    db_manager = DatabaseManager()  # 全局实例，永远不会调用 close()
    ```
    问题说明:
    - 虽然有 close() 方法，但全局实例从不调用
    - 应该使用上下文管理器或在应用关闭时清理

    修复方案：

    在 main.py 的 lifespan 中添加数据库关闭：
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 引擎初始化以及摄像头初始化
        print("Application started")
        face_engine = get_face_engine()
        camera = get_camera()
        db = db_manager  # 获取数据库实例
        back = BackgroundThread()
        back.start()
        yield
        # 引擎销毁以及摄像头销毁
        print("Application shutting down")
        back.stop()
        db.close()  # 关闭数据库连接
        del face_engine
        del camera
    ```
---
1. 文档差异：缺少日志表 

文档要求: backend/docs/后端设计.md 提到需要存储"进出日志"

当前实现: 只有 administrators 和 face_features 表，没有日志表

说明: 文档标注日志功能为可选，这不算严重问题。

---
✅ 做得好的地方：

1. ✅ 使用了正确的表结构（administrators, face_features）
2. ✅ 特征向量正确存储为 BLOB
3. ✅ 提供了完整的增删改查接口
4. ✅ 数据库连接和游标管理正确
5. ✅ 初始化默认管理员的逻辑完善

## 单例 Camera.py 代码审查

1. 严重问题：单例模式实现错误 - init 重复调用

    位置: backend/core/camera.py:10-20
    ```py
    def __new__(cls, index=0):
    if cls.camera is None:
        cls.camera = super().__new__(cls)
    return cls.camera

    def __init__(self, index=0):
    self.index = index
    self.cap = cv2.VideoCapture(index)  # ❌ 每次都会调用！
    if not self.cap.isOpened():
        raise ValueError(f"Failed to open camera{index}")
    ```
    问题说明:
    - 即使 __new__ 返回同一个实例，__init__ 仍然每次都会被调用
    - 每次调用都会执行 cv2.VideoCapture(index)，尝试重复打开摄像头
    - 可能导致：
    - 资源泄漏（旧的VideoCapture未释放）
    - 摄像头访问冲突
    - 重复初始化导致状态丢失

    验证问题:
    cam1 = Camera()  # 第一次：创建实例，打开摄像头
    cam2 = Camera()  # 第二次：返回同一实例，但__init__再次运行，重复打开摄像头！

    修复建议:
    ```py
    def __init__(self, index=0):
    # 添加初始化标志，避免重复初始化
    if hasattr(self, '_initialized'):
        return
    self._initialized = True

    self.index = index
    self.cap = cv2.VideoCapture(index)
    if not self.cap.isOpened():
        raise ValueError(f"Failed to open camera{index}")
    self.first_frame = None
    self.motion_contour_threshold = 500
    ```
---
2. 设计问题：双重单例实现

    位置: backend/core/camera.py:6-13 和 79-91
    ```PY
    # 实现1: 类级别单例
    class Camera:
    camera = None
    def __new__(cls, index=0):
        if cls.camera is None:
            cls.camera = super().__new__(cls)
        return cls.camera

    # 实现2: 模块级别单例
    _camera_instance: Optional[Camera] = None

    def get_camera() -> Camera:
    global _camera_instance
    if _camera_instance is None:
        _camera_instance = Camera()
    return _camera_instance
    ```
    问题说明:
    - 两个单例实现是冗余的
    - 实际使用的是 get_camera()，类的单例逻辑多余
    - 建议只保留一种单例实现

    修复建议: 移除类的单例逻辑，保留 get_camera() 函数式单例

---
3. 逻辑问题：参数命名混乱

    位置: backend/core/camera.py:23, 39, 57, 67
    ```py
    def __init__(self, index=0):
    self.motion_contour_threshold = 500  # 轮廓面积阈值

    def detect_motion(self, prevFrame, frame, motion_threshold):
    # ...
    thresh = cv2.threshold(frame_delta, motion_threshold, 255, ...)  # 二值化阈值
    # ...
    if cv2.contourArea(contour) > self.motion_contour_threshold:  # 轮廓面积阈值
    ```
    问题说明:
    - motion_threshold 参数用于二值化阈值
    - self.motion_contour_threshold 用于轮廓面积阈值
    - 命名相似，容易混淆

    修复建议: 重命名参数
    ```py
    def detect_motion(self, prevFrame, frame, binary_threshold):
    thresh = cv2.threshold(frame_delta, binary_threshold, 255, ...)
    ```
---
4. 代码问题：first_frame 未使用

    位置: backend/core/camera.py:22, 45-46
    ```py
    def __init__(self, index=0):
    self.first_frame = None  # 初始化但从未使用

    def detect_motion(self, prevFrame, frame, motion_threshold):
    if self.first_frame is None:
        self.first_frame = gray  # 赋值但从未读取
    ```
    问题说明:
    - self.first_frame 被初始化和赋值，但从未被使用
    - 实际使用的是 prevFrame 参数
    - 可能是废弃代码

    修复建议: 删除 self.first_frame 相关代码

---
5. 文档问题：与设计文档不符

    设计要求: backend/docs/后端设计.md 提到 GlobalCamera

    当前实现: 类名为 Camera，不是 GlobalCamera

    说明: 这不是错误，只是命名差异，不影响功能

---
✅ 做得好的地方：

1. ✅ 正确实现了摄像头打开和释放
2. ✅ 移动侦测算法实现正确（帧差法）
3. ✅ 提供了 get_camera() 函数式单例接口
4. ✅ 错误处理完善（打开失败时抛出异常）
5. ✅ 使用了适当的图像处理技术（灰度转换、高斯模糊、形态学操作）

---
📝 修复优先级：

| 优先级 | 问题               | 影响                             |
|--------|--------------------|----------------------------------|
| 🔴 P0  | init 重复调用      | 可能导致摄像头访问冲突和资源泄漏 |
| 🟡 P2  | 双重单例实现       | 代码冗余，但不影响功能           |
| 🟢 P3  | 参数命名混乱       | 可读性问题                       |
| 🟢 P3  | first_frame 未使用 | 冗余代码                         |

## backgroundThread.py 代码审查

1. 严重问题：无用的导入

位置: backend/core/backgroundThread.py:6
from pyexpat import features  # ❌ pyexpat 是 XML 解析器，这里不需要

---
2. 严重问题：super().init() 重复调用

位置: backend/core/backgroundThread.py:27-28
def __init__(self, ...):
   super().__init__(target=self.run)  # ❌ 第一次调用
   super().__init__()                  # ❌ 第二次调用，覆盖了第一次的 target

问题说明：
- 第二次调用会覆盖第一次设置的 target=self.run
- 导致线程启动时没有目标函数
- 应该只保留第一次调用

---
3. 设计问题：创建了新的数据库实例

位置: backend/core/backgroundThread.py:34
self.db_manager = manager.DatabaseManager()  # ❌ 新实例

问题说明：
- 全局已有 db_manager 实例（第12行导入）
- 创建新实例会导致多个数据库连接
- 应该使用全局的 db_manager

---
4. 🔴 严重问题：近邻帧算法逻辑错误

位置: backend/core/backgroundThread.py:74-93

# 调用 face_engine 进行人脸识别获得512维特征向量
results = face_engine.extract_feature(img_bytes)
if results is not None:
   logging.info("识别到人脸")
else:
   logging.info("未识别到人脸")

# 与数据库中的特征向量进行比较，判断是否为已知人脸
# 从数据库中获取所有人脸特征
db_results = db_manager.get_face_features()

# 遍历数据库中的每个人脸特征，计算相似度
for item in db_results:
   sim = face_engine.compute_similarity(results, item['feature_vector'])  # ❌ results 可能为 None！

问题说明：
1. 如果 results 为 None（未检测到人脸），仍然会执行第83-93行
2. 第87行 compute_similarity(results, ...) 会因为 results=None 导致错误
3. 应该在检测到人脸后才进行相似度比较

---
5. 优化问题：缺少 prev_frame 更新

位置: backend/core/backgroundThread.py:66-95

if camera.detect_motion(prev_frame, frame, self.motion_threshold):
   logging.info("Move!")
   prev_frame = frame  # ✅ 更新了
   # ... 人脸识别逻辑

time.sleep(self.check_interval)  # ❌ 循环结束，如果没有运动，prev_frame 不更新

问题说明：
- 如果没有检测到运动，prev_frame 不会更新
- 导致后续帧都与同一个旧帧比较
- 应该在每次循环结束前更新 prev_frame

---
6. camera.py 第三点问题：motion_threshold 参数命名

正如我们之前讨论的，在 camera.py 中：
def detect_motion(self, prevFrame, frame, motion_threshold):
   # motion_threshold 用于二值化阈值
   thresh = cv2.threshold(frame_delta, motion_threshold, 255, ...)

但在 backgroundThread.py 中：
def __init__(self, ..., motion_threshold=500, ...):
   self.motion_threshold = motion_threshold

# 使用时
camera.detect_motion(prev_frame, frame, self.motion_threshold)

问题：motion_threshold=500 作为二值化阈值太大了（应该是 25-50），可能是误用了轮廓面积阈值

  📚 后台线程人脸检测原理

  核心流程（近邻帧算法）

  ┌─────────────────────────────────────────────────────┐
  │  1. 持续读取摄像头帧 (100ms 间隔)                    │
  └─────────────────────────────────────────────────────┘
                        ↓
  ┌─────────────────────────────────────────────────────┐
  │  2. 近邻帧运动检测 (比较当前帧与前一帧)               │
  │     - 转换为灰度图                                    │
  │     - 高斯模糊降噪                                    │
  │     - 计算帧差                                        │
  │     - 二值化处理                                      │
  │     - 查找运动轮廓                                    │
  └─────────────────────────────────────────────────────┘
                        ↓
            检测到运动？(Yes)
                        ↓
  ┌─────────────────────────────────────────────────────┐
  │  3. 人脸识别                                          │
  │     - 将帧编码为 JPEG 字节流                          │
  │     - 调用 FaceEngine.extract_feature()              │
  │     - 提取 512 维特征向量                             │
  └─────────────────────────────────────────────────────┘
                        ↓
            识别到人脸？(Yes)
                        ↓
  ┌─────────────────────────────────────────────────────┐
  │  4. 人脸比对                                          │
  │     - 从数据库获取所有已录入人脸特征                   │
  │     - 逐个计算余弦相似度                              │
  │     - 相似度 > 阈值 ？                                │
  └─────────────────────────────────────────────────────┘
                        ↓
            匹配成功？(Yes)
                        ↓
  ┌─────────────────────────────────────────────────────┐
  │  5. 开门                                              │
  │     - 调用 DoorController.open()                     │
  │     - 记录日志（用户名、时间、相似度）                 │
  └─────────────────────────────────────────────────────┘

---
🔧 关键参数详解

1. check_interval (检查间隔)

check_interval = 0.1  # 100ms，即每秒检查10次

作用：控制循环频率
- 太小（如 0.01s）：CPU 占用高，帧处理跟不上
- 太大（如 1s）：响应慢，用户体验差
- 推荐值：0.1 - 0.2 秒

---
2. motion_threshold (移动侦测阈值) ⚠️ 参数命名有歧义

当前代码中有两个不同的阈值混淆了：

A) 二值化阈值 (Binary Threshold)

# 在 camera.detect_motion() 中使用
thresh = cv2.threshold(frame_delta, motion_threshold, 255, cv2.THRESH_BINARY)[1]

作用：判断像素差异是否足够大
- 取值范围：0-255
- 推荐值：25-50
- 值越小，越容易检测到细微运动
- 值越大，只有大幅度运动才会触发

B) 轮廓面积阈值 (Contour Area Threshold)

# 在 Camera 类中定义
self.motion_contour_threshold = 500

# 使用
if cv2.contourArea(contour) > self.motion_contour_threshold:
   return True

作用：过滤小轮廓（如噪声、小虫飞过）
- 取值范围：500-5000 像素
- 推荐值：500-1000
- 值越小，越容易触发
- 值越大，需要更大的运动物体

---
🔴 当前代码的问题：

def __init__(self, check_interval=0.1, motion_threshold=500, ...):
   self.motion_threshold = motion_threshold  # 500

# 使用时
camera.detect_motion(prev_frame, frame, self.motion_threshold)
#                                        └─ 500 作为二值化阈值！❌

问题：motion_threshold=500 被用作二值化阈值（应该是 25-50），导致几乎检测不到运动！

---
3. similarity_threshold (相似度阈值)

similarity_threshold = 0.5  # 0.0 - 1.0 之间

作用：判断两个人脸特征是否匹配
- 取值范围：0.0 - 1.0
- 推荐值：
 - 严格模式：0.6-0.7（更安全，误识率低，但可能拒绝本人）
 - 宽松模式：0.4-0.5（方便，但可能误开门）
- 当前值 0.5：比较宽松

---
🎯 正确的参数设计

建议修改为：

def __init__(self,
            check_interval=0.1,           # 检查间隔：100ms
            binary_threshold=25,          # 二值化阈值：25
            contour_threshold=500,        # 轮廓面积阈值：500
            similarity_threshold=0.6):    # 人脸相似度阈值：0.6

   self.check_interval = check_interval
   self.binary_threshold = binary_threshold      # 用于 detect_motion()
   self.contour_threshold = contour_threshold    # 存储到 Camera 中
   self.similarity_threshold = similarity_threshold

使用时：
camera.detect_motion(prev_frame, frame, self.binary_threshold)

---
🔍 近邻帧算法详细说明

什么是"近邻帧"？

- 近邻帧 = 时间上相邻的两帧图像
- prev_frame = 前一帧
- frame = 当前帧

算法步骤

步骤1：灰度转换

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
prev_gray = cv2.cvtColor(prevFrame, cv2.COLOR_BGR2GRAY)
为什么：彩色图像计算量大，灰度图足够检测运动

步骤2：高斯模糊

gray = cv2.GaussianBlur(gray, (21, 21), 0)
为什么：降噪，减少摄像头传感器噪声的影响

步骤3：计算帧差

frame_delta = cv2.absdiff(prev_gray, gray)
效果：像素值差异大的地方 = 有运动

步骤4：二值化

thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
效果：差异 > 25 的像素设为白色（255），其他为黑色（0）

步骤5：形态学操作

thresh = cv2.dilate(thresh, None, iterations=2)
效果：填充空洞，连接断开的区域

步骤6：查找轮廓

contours, _ = cv2.findContours(thresh, ...)
for contour in contours:
   if cv2.contourArea(contour) > 500:  # 面积足够大
       return True  # 检测到运动

---
📊 参数对比

| 参数                     | 当前值 | 问题    | 推荐值   | 说明                   |
|--------------------------|--------|---------|----------|------------------------|
| check_interval           | 0.1    | ✅ 合理 | 0.1-0.2  | -                      |
| motion_threshold         | 500    | ❌ 错误 | 25-50    | 当前被误用为二值化阈值 |
| motion_contour_threshold | 500    | ✅ 合理 | 500-1000 | 在Camera类中正确使用   |
| similarity_threshold     | 0.5    | ⚠️ 偏低 | 0.6-0.7  | 建议提高安全性         |
