import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, require_admin
from app.models.user import User
from app.schemas.invoice import InvoiceResponse, PaginatedInvoices
from app.services import invoice_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=PaginatedInvoices)
async def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await invoice_service.list_invoices(db, _, page, size)


# /my and /booking/{id} must be registered before /{invoice_id}
@router.get("/my", response_model=PaginatedInvoices)
async def my_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await invoice_service.list_invoices(db, current_user, page, size)


@router.get("/booking/{booking_id}", response_model=InvoiceResponse)
async def get_invoice_by_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await invoice_service.get_invoice_by_booking(db, booking_id, current_user)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await invoice_service.get_invoice(db, invoice_id, current_user)
