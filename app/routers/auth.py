from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user
from app.core.security import create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.user import UserResponse, LoginResponse, UserUpdate, PasswordChange
from app.services import auth_service
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, data)
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer", "user": user}


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.login_user(db, data)
    return {"access_token": result["access_token"], "token_type": "bearer", "user": result["user"]}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_: User = Depends(get_current_user)):
    pass


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await auth_service.update_profile(db, current_user, data)


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await auth_service.change_password(db, current_user, data)
