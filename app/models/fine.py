import enum
import uuid
from decimal import Decimal
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base


class FineStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    waived = "waived"


class Fine(Base):
    __tablename__ = "fines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id"), unique=True, nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    overdue_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    daily_fine_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[FineStatus] = mapped_column(
        SAEnum(FineStatus, name="finestatus"), nullable=False, server_default="pending"
    )
    paid_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    booking  = relationship("Booking", foreign_keys=[booking_id], lazy="raise")
    customer = relationship("User",    foreign_keys=[customer_id], lazy="raise")
