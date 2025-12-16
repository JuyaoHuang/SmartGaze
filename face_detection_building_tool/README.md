# 人脸识别模块 (FaceEngine)

基于 RK3568 + RKNN 的完整人脸识别系统

---

## 项目概述

本项目实现了一个完整的人脸识别模块，包括：
- **RetinaFace** 人脸检测（640×640）
- **人脸对齐** 仿射变换（5个关键点 → 112×112）
- **MobileFaceNet** 特征提取（512维向量）
- **Python ctypes 接口** 便于集成

## 目录结构

```
face_detection/
├── include/
│   ├── face_utils.h              # 数据结构和函数声明
│   └── rknn_box_priors.h         # RetinaFace anchor boxes
├── src/
│   ├── face_engine.cpp           # 主引擎（完整流程）
│   ├── face_aligner.cpp          # 人脸对齐
│   ├── mobilefacenet.cpp         # MobileFaceNet 推理
│   ├── retinaface.cpp            # RetinaFace 人脸检测
│   └── utils.cpp                 # 工具函数
├── utils/                         # rknn_model_zoo 工具库（子项目）
│   ├── CMakeLists.txt            # 子构建文件
│   ├── file_utils.c/h            # 文件读写工具
│   ├── image_utils.c/h           # 图像处理工具
│   ├── image_drawing.c/h         # 图像绘制工具
│   └── audio_utils.c/h           # 音频处理工具
├── models/
│   ├── RetinaFace.rknn          # 人脸检测模型
│   └── mobilefacenet.rknn       # 人脸识别模型
├── third_party/
│   ├── opencv/                  # OpenCV 静态库
│   └── rknn/                    # RKNN 运行时库
├── CMakeLists.txt               # 主构建配置（父项目）
├── CMAKE_ARCHITECTURE.md        # CMake 架构文档
└── test_api.py                  # Python 测试脚本
```

## 已实现的模块

✅ **face_utils.h** - 所有数据结构和函数声明

✅ **face_aligner.cpp** - 人脸对齐（cv::warpAffine）

✅ **mobilefacenet.cpp** - MobileFaceNet RKNN 推理

✅ **retinaface.cpp** - RetinaFace 人脸检测（已修复类型不匹配）

✅ **face_engine.cpp** - 主引擎（整合检测+对齐+识别）

✅ **utils.cpp** - 工具函数（文件读取、余弦相似度）

✅ **utils/** - rknn_model_zoo 工具库（子项目，静态库）

✅ **test_api.py** - Python ctypes 测试脚本

✅ **CMakeLists.txt** - 编译配置（OpenCV 静态库 + find_package + add_subdirectory）

---

## 编译步骤

### 1. 准备环境

确保以下文件已就位：
- `third_party/opencv/` - OpenCV 静态库 + cmake 配置
- `third_party/rknn/` - RKNN 运行时库
- `models/RetinaFace.rknn` - 模型文件
- `models/mobilefacenet.rknn` - 模型文件
- `utils/` - rknn_model_zoo 工具库（包含 CMakeLists.txt）

### 2. 编译

```bash
cd face_detection
mkdir -p build
cd build
cmake ..
make -j4
```

**生成文件**：
- `build/libface_engine.so` - 主动态库（包含所有功能 + OpenCV 静态库）
- `build/utils/libfileutils.a` - 文件工具静态库（已链接到 .so）
- `build/utils/libimageutils.a` - 图像工具静态库（已链接到 .so）

**部署到 RK3568**：
只需传输 `libface_engine.so` 和 `models/*.rknn` 文件即可。

---

## 使用方法

### Python 接口

```bash
# 1. 单张图片特征提取
python test_api.py --image test.jpg

# 2. 两张图片人脸比对
python test_api.py --image person1.jpg --image2 person2.jpg

# 3. 指定模型路径
python test_api.py --image test.jpg \
    --retinaface ./models/RetinaFace.rknn \
    --mobilefacenet ./models/mobilefacenet.rknn
```

### Python 代码示例

```python
from test_api import FaceEngine

# 初始化引擎
engine = FaceEngine(
    retinaface_model="./models/RetinaFace.rknn",
    mobilefacenet_model="./models/mobilefacenet.rknn"
)

# 提取特征向量
feature = engine.extract_feature("test.jpg")  # 返回 512 维 numpy 数组

# 比对两张人脸
feature1 = engine.extract_feature("person1.jpg")
feature2 = engine.extract_feature("person2.jpg")
similarity = engine.compare_faces(feature1, feature2)

print(f"Similarity: {similarity:.4f}")
if similarity > 0.5:
    print("Same person!")
else:
    print("Different person")
```

---

## C++ 接口

```cpp
#include "face_utils.h"

// 1. 创建引擎
void* engine = FaceEngine_Create();

// 2. 初始化模型
FaceEngine_Init(engine, "RetinaFace.rknn", "mobilefacenet.rknn");

// 3. 提取特征
float feature[512];
int ret = FaceEngine_ExtractFeature(engine, jpeg_data, data_len, feature);

// 4. 计算相似度
float similarity = FaceEngine_CosineSimilarity(feature1, feature2);

// 5. 销毁引擎
FaceEngine_Destroy(engine);
```

---

## 数据流程

```
JPEG 图片
   ↓
[解码] → BGR 图像
   ↓
[RetinaFace] → 人脸框 + 5个关键点
   ↓
[人脸对齐] → 112×112 RGB 图像
   ↓
[MobileFaceNet] → 512 维特征向量
   ↓
[余弦相似度] → 判断是否同一人
```

---

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| RetinaFace 输入 | 640×640 RGB | 人脸检测模型输入 |
| MobileFaceNet 输入 | 112×112 RGB | 人脸识别模型输入 |
| 特征向量维度 | 512 | MobileFaceNet 输出 |
| 相似度阈值（严格） | 0.5 | 门禁系统推荐 |
| 相似度阈值（一般） | 0.3 | 通用场景推荐 |

---

## 常见问题

### Q: 编译时找不到 OpenCV？
**A**: 确保 `third_party/opencv/lib/cmake/opencv4/OpenCVConfig.cmake` 存在。

### Q: 编译时找不到 RKNN？
**A**: 确保 `third_party/rknn/lib/librknnrt.so` 存在。

### Q: 编译时找不到 utils 工具库？
**A**:
1. 确保 `utils/CMakeLists.txt` 存在
2. 检查 `utils/file_utils.c` 和 `utils/image_utils.c` 是否存在
3. CMake 会自动通过 `add_subdirectory(utils)` 构建子项目

### Q: 运行时提示 "No face detected"？
**A**:
1. 确保图片中有清晰的人脸
2. 检查 RetinaFace 模型是否正确加载
3. 降低置信度阈值（修改 `CONF_THRESHOLD` in retinaface.cpp）

### Q: 如何提高识别准确率？
**A**:
1. 录入时采集多角度人脸
2. 确保光照均匀
3. 调整相似度阈值
4. 使用更高分辨率的图片

---

## 性能说明

- **RetinaFace 推理时间**: ~20-50ms (RK3568 NPU)
- **MobileFaceNet 推理时间**: ~5-15ms (RK3568 NPU)
- **人脸对齐时间**: ~1-3ms (CPU)
- **总耗时**: ~30-70ms

---

## 参考文档

- [face_detection.md](../face_detection.md) - 完整开发文档
- [CMAKE_ARCHITECTURE.md](./CMAKE_ARCHITECTURE.md) - CMake 架构说明
- [RKNN_MODEL_SPEC.md](./docs/RKNN_MODEL_SPEC.md) - 模型输入输出规范

---

## 项目架构

### CMake 层次结构

```
父 CMakeLists.txt (face_detection/CMakeLists.txt)
  ├── 配置 OpenCV (find_package)
  ├── 配置 RKNN (手动配置)
  ├── 添加子项目: add_subdirectory(utils)
  │   └─> utils/CMakeLists.txt 构建静态库
  ├── 编译主项目源文件 (src/*.cpp)
  └── 生成 libface_engine.so
```

详细说明请参考 [CMAKE_ARCHITECTURE.md](./CMAKE_ARCHITECTURE.md)

---

## 开发者

Juyao Huang
更新时间: 2025-12-15
版本: v2.0

**版本历史**：
- v1.0 (2025-12-15): 初始版本，实现核心功能
- v2.0 (2025-12-15): 完成 RetinaFace 集成，修复类型不匹配，优化 CMake 架构
