#!/usr/bin/env python3
"""
人脸识别 FaceEngine Python 测试脚本
使用 ctypes 调用 libface_engine.so

Usage:
    python test_api.py --image test.jpg

"""

import ctypes
import numpy as np
import argparse
import os
import sys

# ========================================
# 配置
# ========================================
LIB_PATH = "./build/libface_engine.so"  # 动态库路径
RETINAFACE_MODEL = "./models/RetinaFace.rknn"
MOBILEFACENET_MODEL = "./models/mobilefacenet.rknn"

# ========================================
# 加载动态库
# ========================================
try:
    lib = ctypes.CDLL(LIB_PATH)
    print(f"✓ Successfully loaded library: {LIB_PATH}")
except OSError as e:
    print(f"✗ Error: Failed to load library {LIB_PATH}")
    print(f"  {e}")
    print("\nPlease compile the library first:")
    print("  cd face_detection && mkdir -p build && cd build && cmake .. && make -j4")
    sys.exit(1)

# ========================================
# 定义函数签名
# ========================================

# void* FaceEngine_Create()
lib.FaceEngine_Create.restype = ctypes.c_void_p
lib.FaceEngine_Create.argtypes = []

# int FaceEngine_Init(void* engine, const char* retinaface_model, const char* mobilefacenet_model)
lib.FaceEngine_Init.restype = ctypes.c_int
lib.FaceEngine_Init.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]

# int FaceEngine_ExtractFeature(void* engine, unsigned char* jpeg_data, int data_len, float* feature_512)
lib.FaceEngine_ExtractFeature.restype = ctypes.c_int
lib.FaceEngine_ExtractFeature.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_float)
]

# void FaceEngine_Destroy(void* engine)
lib.FaceEngine_Destroy.restype = None
lib.FaceEngine_Destroy.argtypes = [ctypes.c_void_p]

# float FaceEngine_CosineSimilarity(const float* emb1, const float* emb2)
lib.FaceEngine_CosineSimilarity.restype = ctypes.c_float
lib.FaceEngine_CosineSimilarity.argtypes = [
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float)
]

# ========================================
# FaceEngine 类封装
# ========================================

class FaceEngine:
    def __init__(self, retinaface_model, mobilefacenet_model):
        """初始化人脸识别引擎"""
        self.engine = None
        self.retinaface_model = retinaface_model
        self.mobilefacenet_model = mobilefacenet_model

        # 创建引擎实例
        self.engine = lib.FaceEngine_Create()
        if not self.engine:
            raise RuntimeError("Failed to create FaceEngine instance")

        # 初始化模型
        print(f"Initializing FaceEngine...")
        print(f"  RetinaFace model: {retinaface_model}")
        print(f"  MobileFaceNet model: {mobilefacenet_model}")

        ret = lib.FaceEngine_Init(
            self.engine,
            retinaface_model.encode('utf-8'),
            mobilefacenet_model.encode('utf-8')
        )

        if ret != 0:
            lib.FaceEngine_Destroy(self.engine)
            raise RuntimeError(f"Failed to initialize FaceEngine (ret={ret})")

        print("✓ FaceEngine initialized successfully")

    def extract_feature(self, image_path):
        """
        提取人脸特征向量

        Args:
            image_path: 图片文件路径（JPEG格式）

        Returns:
            numpy.ndarray: 512维特征向量，失败返回 None
        """
        if not os.path.exists(image_path):
            print(f"✗ Error: Image file not found: {image_path}")
            return None

        # 读取 JPEG 文件
        with open(image_path, 'rb') as f:
            jpeg_data = f.read()

        # 转换为 ctypes 数组
        jpeg_array = np.frombuffer(jpeg_data, dtype=np.uint8)
        jpeg_ptr = jpeg_array.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

        # 准备输出缓冲区
        feature_512 = np.zeros(512, dtype=np.float32)
        feature_ptr = feature_512.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

        # 调用 C++ 函数
        print(f"\nExtracting feature from: {image_path}")
        ret = lib.FaceEngine_ExtractFeature(self.engine, jpeg_ptr, len(jpeg_data), feature_ptr)

        if ret == 0:
            print("✓ Feature extracted successfully")
            print(f"  Feature shape: {feature_512.shape}")
            print(f"  Feature norm: {np.linalg.norm(feature_512):.4f}")
            print(f"  Feature range: [{feature_512.min():.4f}, {feature_512.max():.4f}]")
            return feature_512
        elif ret == -1:
            print("✗ Error: No face detected in the image")
            return None
        else:
            print(f"✗ Error: Feature extraction failed (ret={ret})")
            return None

    def compare_faces(self, feature1, feature2):
        """
        比较两个人脸特征向量的相似度

        Args:
            feature1: 512维特征向量1
            feature2: 512维特征向量2

        Returns:
            float: 余弦相似度 [0, 1]
        """
        if feature1 is None or feature2 is None:
            return 0.0

        ptr1 = feature1.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        ptr2 = feature2.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

        similarity = lib.FaceEngine_CosineSimilarity(ptr1, ptr2)
        return float(similarity)

    def __del__(self):
        """释放资源"""
        if self.engine:
            lib.FaceEngine_Destroy(self.engine)
            print("\n✓ FaceEngine destroyed")

# ========================================
# 主函数
# ========================================

def main():
    parser = argparse.ArgumentParser(description="FaceEngine Python Test Script")
    parser.add_argument('--image', type=str, required=True, help="Input image path (JPEG)")
    parser.add_argument('--image2', type=str, default=None, help="Second image for comparison (optional)")
    parser.add_argument('--retinaface', type=str, default=RETINAFACE_MODEL, help="RetinaFace model path")
    parser.add_argument('--mobilefacenet', type=str, default=MOBILEFACENET_MODEL, help="MobileFaceNet model path")

    args = parser.parse_args()

    # 检查模型文件是否存在
    if not os.path.exists(args.retinaface):
        print(f"✗ Error: RetinaFace model not found: {args.retinaface}")
        return

    if not os.path.exists(args.mobilefacenet):
        print(f"✗ Error: MobileFaceNet model not found: {args.mobilefacenet}")
        return

    # 创建 FaceEngine 实例
    try:
        engine = FaceEngine(args.retinaface, args.mobilefacenet)
    except RuntimeError as e:
        print(f"✗ {e}")
        return

    # 提取第一张图片的特征
    feature1 = engine.extract_feature(args.image)
    if feature1 is None:
        return

    # 如果提供了第二张图片，进行比对
    if args.image2:
        feature2 = engine.extract_feature(args.image2)
        if feature2 is not None:
            similarity = engine.compare_faces(feature1, feature2)
            print(f"\n{'='*50}")
            print(f"Face Comparison Result:")
            print(f"  Image 1: {args.image}")
            print(f"  Image 2: {args.image2}")
            print(f"  Cosine Similarity: {similarity:.4f}")
            print(f"  Judgment: {'Same person ✓' if similarity > 0.5 else 'Different person ✗'}")
            print(f"  (Threshold: 0.5 for strict, 0.3 for general)")
            print(f"{'='*50}")
    else:
        # 只提取特征，打印前10个值作为示例
        print(f"\nFeature vector (first 10 values):")
        print(f"  {feature1[:10]}")

    print("\n✓ Test completed successfully!")

if __name__ == "__main__":
    main()
