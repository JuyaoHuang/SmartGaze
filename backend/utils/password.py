"""密码工具模块

开发模式：使用明文密码存储（仅用于测试，生产环境应使用加密）
"""


def hash_password(password: str) -> str:
    """存储密码（明文）

    Args:
        password: 明文密码

    Returns:
        明文密码字符串
    """
    return password


def verify_password(plain_password: str, stored_password: str) -> bool:
    """验证密码是否正确

    Args:
        plain_password: 用户输入的明文密码
        stored_password: 数据库中存储的密码

    Returns:
        密码正确返回 True，否则返回 False
    """
    return plain_password == stored_password
