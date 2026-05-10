import uuid
import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, Enum as SAEnum, Numeric, SmallInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class VehicleCategory(str, enum.Enum):
    economy = "economy"
    standard = "standard"
    premium = "premium"
    suv = "suv"
    van = "van"


class FuelType(str, enum.Enum):
    petrol = "petrol"
    diesel = "diesel"
    electric = "electric"
    hybrid = "hybrid"


class VehicleStatus(str, enum.Enum):
    available = "available"
    booked = "booked"
    maintenance = "maintenance"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    license_plate: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    category: Mapped[VehicleCategory] = mapped_column(
        SAEnum(VehicleCategory, name="vehiclecategory"), nullable=False
    )
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fuel_type: Mapped[FuelType | None] = mapped_column(
        SAEnum(FuelType, name="fueltype"), nullable=True
    )
    seats: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(VehicleStatus, name="vehiclestatus"),
        nullable=False,
        server_default=VehicleStatus.available.value,
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
