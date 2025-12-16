import logging
import threading
import time
from typing import Optional


class DoorController:
    '''单例模式'''
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, status: bool = False):
        if not cls._instance:
            with cls._lock:  # 使用类锁确保多线程环境下的单例安全
                if not cls._instance:  # 双重检查锁定模式
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, status: bool = False):
        # 初始化只在第一次创建实例时执行
        if not hasattr(self, '_initialized'):
            self.status = status  # 当前门状态：False-关闭，True-打开
            self._door_lock = threading.Lock()  # 实例级别的线程锁，用于控制开门操作
            self._initialized = True

    def open(self):
        # 尝试获取锁，如果已被锁定则直接返回
        if not self._door_lock.acquire(blocking=False):
            logging.info("Door  is busy")

        try:
            logging.info("Open the door")
            # TODO: 调用 GPIO 控制开门的实际硬件操作
            self.status = True

            # 保持门打开3秒
            time.sleep(3)

            # 执行关锁操作
            logging.info("Close the door")
            # TODO: 调用 GPIO 控制关锁的实际硬件操作
            self.status = False

        finally:
            # 确保无论是否发生异常，都能释放锁
            self._door_lock.release()
# ========================================
# 全局单例实例（供 FastAPI 使用）
# ========================================

# 延迟初始化：只在首次调用时创建实例
_door_controller_instance: Optional[DoorController] = None


def get_door_controller() -> DoorController:
    """
    获取全局 DoorController 实例（单例模式）

    供 FastAPI 路由函数调用
    """
    global _door_controller_instance
    if _door_controller_instance is None:
        _door_controller_instance = DoorController()
    return _door_controller_instance
