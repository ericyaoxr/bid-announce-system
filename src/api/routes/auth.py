from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from src.api.deps import CurrentUser, DbSession
from src.core.security import create_access_token, get_password_hash, verify_password
from src.db.models import User

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    is_admin: bool = False


class RegisterRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: DbSession):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已禁用",
        )
    token = create_access_token(data={"sub": user.username})
    return TokenResponse(
        access_token=token,
        username=user.username,
        is_admin=user.is_admin,
    )


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: DbSession):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    is_first_user = (await db.execute(select(User))).scalars().first() is None
    user = User(
        username=req.username,
        hashed_password=get_password_hash(req.password),
        is_admin=is_first_user,
    )
    db.add(user)
    await db.flush()
    token = create_access_token(data={"sub": user.username})
    return TokenResponse(
        access_token=token,
        username=user.username,
        is_admin=user.is_admin,
    )


@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, db: DbSession, user: CurrentUser):
    if not verify_password(req.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )
    user.hashed_password = get_password_hash(req.new_password)
    await db.flush()
    return {"message": "密码修改成功"}


@router.get("/me")
async def get_me(user: CurrentUser):
    return {
        "username": user.username,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
    }
