"""
数据库连接
=========
SQLite 数据库，文件在 data/users.db，首次启动自动创建。

使用方式：
    from app.database import SessionLocal, engine, Base
    from app.models import User
    Base.metadata.create_all(bind=engine)   # 建表（已有则跳过）
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/users.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 允许多线程
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
