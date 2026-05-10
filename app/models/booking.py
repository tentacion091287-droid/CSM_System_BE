import enum
import uuid
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Date, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.db.session import Base


class BookingStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
    rejected = "rejected"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("return_date > pickup_date", name="chk_dates"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True
    )
    pickup_date: Mapped[object] = mapped_column(Date, nullable=False)
    return_date: Mapped[object] = mapped_column(Date, nullable=False)
    actual_return: Mapped[object | None] = mapped_column(Date, nullable=True)
    pickup_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    drop_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    needs_driver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="bookingstatus"), nullable=False, server_default="pending"
    )
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    vehicle  = relationship("Vehicle",      foreign_keys=[vehicle_id],  lazy="raise")
    customer = relationship("User",         foreign_keys=[customer_id], lazy="raise")
    driver   = relationship("Driver",       foreign_keys=[driver_id],   lazy="raise")
    rating   = relationship("DriverRating", foreign_keys="DriverRating.booking_id", uselist=False, lazy="raise")

    @property
    def driver_rated(self) -> bool:
        return self.rating is not None
