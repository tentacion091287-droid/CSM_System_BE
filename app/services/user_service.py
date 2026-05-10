import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.user import User, UserRole


async def list_users(db: AsyncSession, page: int = 1, size: int = 20) -> dict:
    offset = (page - 1) * size
    result = await db.execute(
        select(User).where(User.is_deleted == False).offset(offset).limit(size)
    )
    users = result.scalars().all()
    count_result = await db.execute(
        select(func.count()).select_from(User).where(User.is_deleted == False)
    )
    total = count_result.scalar()
    return {
        "items": users,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def toggle_active(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await get_user(db, user_id)
    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)
    return user


async def change_role(db: AsyncSession, user_id: uuid.UUID, role: UserRole) -> User:
    user = await get_user(db, user_id)
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user
