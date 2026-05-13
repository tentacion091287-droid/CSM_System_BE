import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, require_admin
from app.models.booking import BookingStatus
from app.models.user import User
from app.schemas.booking import (
    AssignDriverRequest,
    BookingComplete,
    BookingCreate,
    BookingReject,
    BookingResponse,
    BookingUpdate,
    PaginatedBookings,
)
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await booking_service.create_booking(db, data, current_user)


@router.get("/", response_model=PaginatedBookings)
async def list_bookings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: BookingStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await booking_service.list_bookings(db, current_user, page, size, status)


# /history must be registered before /{booking_id} to avoid UUID parse failure
@router.get("/history", response_model=PaginatedBookings)
async def get_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await booking_service.get_history(db, current_user, page, size)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await booking_service.get_booking(db, booking_id, current_user)


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: uuid.UUID,
    data: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await booking_service.update_booking(db, booking_id, data, current_user)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await booking_service.cancel_booking(db, booking_id, current_user)


@router.patch("/{booking_id}/approve", response_model=BookingResponse)
async def approve_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await booking_service.approve_booking(db, booking_id)


@router.patch("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: uuid.UUID,
    data: BookingReject,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await booking_service.reject_booking(db, booking_id, data)


@router.patch("/{booking_id}/activate", response_model=BookingResponse)
async def activate_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await booking_service.activate_booking(db, booking_id)


@router.patch("/{booking_id}/complete", response_model=BookingResponse)
async def complete_booking(
    booking_id: uuid.UUID,
    data: BookingComplete,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await booking_service.complete_booking(db, booking_id, data)


@router.patch("/{booking_id}/assign-driver", response_model=BookingResponse)
async def assign_driver(
    booking_id: uuid.UUID,
    data: AssignDriverRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await booking_service.assign_driver(db, booking_id, data)
