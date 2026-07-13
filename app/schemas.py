"""
请求 / 响应 Schema
=================
Pydantic 模型，FastAPI 自动校验输入、过滤返回字段。

注意：
  - 所有返回给前端的 Schema 不包含 password_hash
  - 注册时 phone/email 至少填一个
  - 修改资料时所有字段可选，只更新传了值的字段
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ============================================================
#  注册
# ============================================================

class UserRegister(BaseModel):
    username: str
    password: str
    phone: Optional[str] = None
    email: Optional[str] = None
    nickname: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("用户名不能为空")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码至少6位")
        return v

    @field_validator("phone")
    @classmethod
    def phone_or_email_required(cls, v: Optional[str], info) -> Optional[str]:
        """校验 phone 和 email 至少一个不为空（Pydantic 逐字段校验，
        这里只能取当前字段的值，联合校验放在 auth.py 里做）"""
        return v


# ============================================================
#  登录
# ============================================================

class UserLogin(BaseModel):
    login_type: str   # "username" | "phone" | "email"
    account: str
    password: str

    @field_validator("login_type")
    @classmethod
    def valid_login_type(cls, v: str) -> str:
        if v not in ("username", "phone", "email"):
            raise ValueError("login_type 必须是 username / phone / email")
        return v


# ============================================================
#  返回给前端的用户信息（不含密码哈希）
# ============================================================

class UserResponse(BaseModel):
    id: int
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ============================================================
#  登录成功返回
# ============================================================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============================================================
#  修改个人资料
# ============================================================

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


# ============================================================
#  修改密码
# ============================================================

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("新密码至少6位")
        return v
