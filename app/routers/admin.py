import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, require_admin
from app.schemas.dashboard import DashboardResponse
from app.schemas.user import UserResponse, PaginatedUsers, RoleUpdate
from app.models.user import User
from app.services import user_service, dashboard_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await dashboard_service.get_dashboard(db)


@router.get("/users", response_model=PaginatedUsers)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await user_service.list_users(db, page, size)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await user_service.get_user(db, user_id)


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def toggle_activate(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await user_service.toggle_active(db, user_id)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def change_role(
    user_id: uuid.UUID,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await user_service.change_role(db, user_id, data.role)
