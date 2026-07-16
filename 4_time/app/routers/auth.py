"""
用户认证接口
============
POST   /api/auth/register   注册
POST   /api/auth/login      登录（支持 username/phone/email 三种账号类型）
GET    /api/auth/me         获取当前登录用户信息
PUT    /api/auth/profile    修改个人资料
PUT    /api/auth/password   修改密码
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import User
from app.schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    UserUpdate, PasswordUpdate,
)
from app.security import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
)

router = APIRouter()


# ============================================================
#  数据库会话依赖（每个请求自动开启和关闭）
# ============================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
#  JWT 鉴权依赖（需要 Bearer Token 的接口用）
# ============================================================

def get_current_user(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    """从 Authorization Header 中解析 token → 查出当前用户。
    任何一个环节失败都返回 401。
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供有效的认证令牌")
    token = authorization[7:]  # 去掉 "Bearer " 前缀
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ============================================================
#  POST /api/auth/register
# ============================================================

@router.post("/register", response_model=UserResponse, summary="用户注册")
def register(data: UserRegister, db: Session = Depends(get_db)):
    # 唯一性检查（手动查，比捕获 IntegrityError 更友好）
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已被注册")
    if data.phone and db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="手机号已被注册")
    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        phone=data.phone or None,
        email=data.email or None,
        nickname=data.nickname or None,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="注册失败，请检查字段是否重复")
    return user


# ============================================================
#  POST /api/auth/login
# ============================================================

@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(data: UserLogin, db: Session = Depends(get_db)):
    # 根据 login_type 选择查询字段
    if data.login_type == "username":
        user = db.query(User).filter(User.username == data.account).first()
    elif data.login_type == "phone":
        user = db.query(User).filter(User.phone == data.account).first()
    else:  # email
        user = db.query(User).filter(User.email == data.account).first()

    # 账号不存在或密码错误 → 统一 401（防止账号枚举）
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=user)


# ============================================================
#  GET /api/auth/me
# ============================================================

@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    """前端刷新页面后恢复登录态"""
    return current_user


# ============================================================
#  PUT /api/auth/profile
# ============================================================

@router.put("/profile", response_model=UserResponse, summary="修改个人资料")
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 只更新传了值的字段
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.avatar is not None:
        current_user.avatar = data.avatar
    if data.bio is not None:
        current_user.bio = data.bio
    if data.phone is not None:
        # 检查手机号是否被其他用户占用
        existing = db.query(User).filter(
            User.phone == data.phone, User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="手机号已被其他用户使用")
        current_user.phone = data.phone
    if data.email is not None:
        existing = db.query(User).filter(
            User.email == data.email, User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        current_user.email = data.email

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="修改失败，字段可能重复")
    return current_user


# ============================================================
#  PUT /api/auth/password
# ============================================================

@router.put("/password", summary="修改密码")
def update_password(
    data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "密码修改成功"}
