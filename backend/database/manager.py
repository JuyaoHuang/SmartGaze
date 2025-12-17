import sqlite3
import numpy as np
from typing import Optional, Dict, List


class DatabaseManager:
    """数据库管理器类，负责处理所有数据库操作"""

    def __init__(self, db_path: str = 'sm_door.db'):
        """初始化数据库连接"""
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """创建管理员表和人脸特征表"""
        # 1. 管理员信息表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS administrators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # 2. 人脸特征向量表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                feature_vector BLOB NOT NULL  -- 存储512维特征向量的二进制数据
            )
        ''')

        self.conn.commit()

    def add_administrator(self, username: str, password: str) -> int:
        """添加管理员"""
        self.cursor.execute('''
            INSERT INTO administrators (username, password)
            VALUES (?, ?)
        ''', (username, password))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_administrator(self, username: str) -> str:
        """通过用户名获取管理员信息"""
        self.cursor.execute('''
            SELECT id, username, password
            FROM administrators
            WHERE username = ?
        ''', username)
        row = self.cursor.fetchone()
        if row:
            return row[2]
        return ""

    def update_administrator_password(self, username: str, new_password: str) -> bool:
        """更新管理员密码"""
        try:
            self.cursor.execute('''
                UPDATE administrators
                SET password = ?
                WHERE username = ?
            ''', (new_password, username))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"更新管理员密码失败: {e}")
            return False


    def get_face_name_list(self) -> List[str]:
        """获取所有用户名列表"""
        self.cursor.execute('''
            SELECT name FROM face_features
        ''')
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]

    def delete_face_name(self, name: str) -> bool:
        """删除指定用户名的人脸特征向量"""
        try:
            self.cursor.execute('''
                DELETE FROM face_features
                WHERE name = ?
            ''', name)
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"删除人脸特征向量失败: {e}")
            return False

    def delete_all_face_names(self) -> bool:
        """删除所有用户名的人脸特征向量"""
        try:
            self.cursor.execute('''
                DELETE FROM face_features
            ''')
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"删除所有人脸特征向量失败: {e}")
            return False



    def add_face_feature(self, name: str, feature_vector: np.ndarray) -> bool:
        """添加人脸特征向量"""
        # 将numpy数组转换为二进制数据
        feature_blob = feature_vector.tobytes()

        try:
            self.cursor.execute('''
                INSERT INTO face_features (name, feature_vector)
                VALUES (?, ?)
            ''', (name, feature_blob))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加人脸特征向量失败: {e}")
            return False

    def get_face_features(self) -> List[Dict]:
        """获取所有人脸特征向量"""
        self.cursor.execute('''
            SELECT id, name, feature_vector
            FROM face_features
        ''')
        rows = self.cursor.fetchall()
        features = []
        for row in rows:
            # 将二进制数据转换回numpy数组
            feature_vector = np.frombuffer(row[2], dtype=np.float32)
            features.append({
                'id': row[0],
                'name': row[1],
                'feature_vector': feature_vector
            })
        return features

    def close(self):
        """关闭数据库连接"""
        self.conn.close()


# 创建全局数据库管理器实例
db_manager = DatabaseManager()


def init_database():
    """初始化数据库，创建默认管理员"""
    # 检查是否已有管理员
    admin = db_manager.get_administrator('admin')
    if not admin:
        default_password = '123456'
        db_manager.add_administrator(
            username='admin',
            password=default_password,
        )
        print("默认管理员已创建：用户名=admin, 密码=123456")
