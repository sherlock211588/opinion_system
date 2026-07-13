"""
用户表 ORM 模型
==============
数据库文件 data/users.db，表名 users。

约束：
  - username 必填、唯一
  - phone 和 email 至少一个不为空（由 schemas.py 校验）
  - phone、email 如果填写必须唯一
  - password_hash 存储 bcrypt 哈希，绝不存明文
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    nickname = Column(String(50), nullable=True)
    avatar = Column(String(500), nullable=True)
    bio = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
