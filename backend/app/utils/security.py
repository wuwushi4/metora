# -*- coding: utf-8 -*-
"""
安全工具模組
提供密碼加密、驗證等安全相關功能
"""
import bcrypt

# ===========================================
# 密碼加密配置
# ===========================================
# 使用 bcrypt 演算法進行密碼加密
# - bcrypt 是目前最推薦的密碼雜湊演算法之一
# - 自動加鹽（salt），防止彩虹表攻擊
# - 計算成本可調，可隨硬體進步而調整
# ===========================================


def hash_password(password: str) -> str:
    """
    將明文密碼進行雜湊加密

    Args:
        password: 明文密碼

    Returns:
        加密後的密碼雜湊值

    Example:
        >>> hashed = hash_password("my_secret_password")
        >>> print(hashed)
        $2b$12$...
    """
    # 將密碼轉換為 bytes
    password_bytes = password.encode('utf-8')
    # 生成 salt 並進行雜湊
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # 返回字串形式
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    驗證明文密碼與雜湊密碼是否匹配

    Args:
        plain_password: 使用者輸入的明文密碼
        hashed_password: 資料庫中儲存的雜湊密碼

    Returns:
        True 表示密碼正確，False 表示密碼錯誤

    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    # 將密碼和雜湊值轉換為 bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # 驗證密碼
    return bcrypt.checkpw(password_bytes, hashed_bytes)
