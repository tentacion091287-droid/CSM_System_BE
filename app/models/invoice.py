import uuid
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id"), unique=True, nullable=False
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id"), unique=True, nullable=False
    )
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rental_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fine_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default="0.00"
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default="0.00"
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    issued_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    booking = relationship("Booking", foreign_keys=[booking_id], lazy="raise")
    payment = relationship("Payment", foreign_keys=[payment_id], lazy="raise")

    @property
    def customer(self):
        return self.payment.customer if self.payment else None
