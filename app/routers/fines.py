import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, require_admin
from app.models.fine import FineStatus
from app.models.user import User
from app.schemas.fine import FineResponse, PaginatedFines
from app.services import fine_service

router = APIRouter(prefix="/fines", tags=["fines"])


@router.get("/", response_model=PaginatedFines)
async def list_fines(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: FineStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await fine_service.list_fines(db, current_user, page, size, status)


# /my and /booking/{id} must be registered before /{fine_id}
@router.get("/my", response_model=PaginatedFines)
async def my_fines(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: FineStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await fine_service.list_fines(db, current_user, page, size, status)


@router.get("/booking/{booking_id}", response_model=FineResponse)
async def get_fine_by_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await fine_service.get_fine_by_booking(db, booking_id, current_user)


@router.get("/{fine_id}", response_model=FineResponse)
async def get_fine(
    fine_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await fine_service.get_fine(db, fine_id, current_user)


@router.patch("/{fine_id}/waive", response_model=FineResponse)
async def waive_fine(
    fine_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await fine_service.waive_fine(db, fine_id)


@router.patch("/{fine_id}/pay", response_model=FineResponse)
async def pay_fine(
    fine_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await fine_service.pay_fine(db, fine_id, current_user)
