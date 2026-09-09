from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models import User
from app.schemas.user import Token, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["用户与鉴权"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession) -> User:
    existing = db.scalar(
        select(User).where(or_(User.username == payload.username, User.email == payload.email))
    )
    if existing:
        raise HTTPException(status_code=409, detail="用户名或邮箱已注册")

    is_first_user = (db.scalar(select(func.count(User.id))) or 0) == 0
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        is_admin=is_first_user,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="用户名或邮箱已注册") from exc
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    user = db.scalar(
        select(User).where(or_(User.username == form.username, User.email == form.username))
    )
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")
    return Token(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def read_me(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, db: DbSession, user: CurrentUser) -> User:
    values = payload.model_dump(exclude_unset=True)
    if "email" in values and values["email"] != user.email:
        existing = db.scalar(select(User.id).where(User.email == values["email"]))
        if existing:
            raise HTTPException(status_code=409, detail="邮箱已被使用")
        user.email = values["email"]
    if "full_name" in values:
        user.full_name = values["full_name"]
    if values.get("password"):
        user.hashed_password = get_password_hash(values["password"])
    db.commit()
    db.refresh(user)
    return user
