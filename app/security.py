"""
密码加密 + JWT 令牌
===================
bcrypt 哈希密码，PyJWT 签发和验证 token。
"""

import os
from datetime import datetime, timedelta

import bcrypt
import jwt

# JWT 密钥（32字节以上，满足 HS256 最低要求）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "opinion_system_secret_key_2026_long_enough_32bytes")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """明文 -> bcrypt 哈希"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """比对明文和哈希是否匹配"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(user_id: int) -> str:
    """用 user_id 签发 JWT，默认 7 天过期"""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """验证 JWT，成功返回 user_id，失败返回 None"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub", 0))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        return None
