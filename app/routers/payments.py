import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, require_admin
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaginatedPayments
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await payment_service.initiate_payment(db, data, current_user)


@router.get("/", response_model=PaginatedPayments)
async def list_payments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await payment_service.list_payments(db, current_user, page, size)


@router.get("/my", response_model=PaginatedPayments)
async def my_payments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await payment_service.list_payments(db, current_user, page, size)


# /my must be registered before /{payment_id} to avoid UUID parse failure
@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await payment_service.get_payment(db, payment_id, current_user)


@router.patch("/{payment_id}/process", response_model=PaymentResponse)
async def process_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await payment_service.process_payment(db, payment_id)


@router.patch("/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await payment_service.refund_payment(db, payment_id)
