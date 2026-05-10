import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, require_admin
from app.models.user import User
from app.schemas.driver import (
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverAvailabilityUpdate,
    PaginatedDrivers,
)
from app.schemas.driver_rating import RatingCreate, RatingResponse, PaginatedRatings
from app.services import driver_service, driver_rating_service

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=PaginatedDrivers)
async def list_drivers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await driver_service.list_drivers(db, page, size)


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await driver_service.get_driver(db, driver_id)


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    data: DriverCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await driver_service.create_driver(db, data)


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: uuid.UUID,
    data: DriverUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await driver_service.update_driver(db, driver_id, data)


@router.patch("/{driver_id}/availability", response_model=DriverResponse)
async def toggle_availability(
    driver_id: uuid.UUID,
    data: DriverAvailabilityUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await driver_service.toggle_availability(db, driver_id, data)


@router.get("/{driver_id}/ratings", response_model=PaginatedRatings)
async def get_driver_ratings(
    driver_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await driver_rating_service.list_driver_ratings(db, driver_id, page, size)


@router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def submit_rating(
    data: RatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await driver_rating_service.submit_rating(db, data, current_user)
