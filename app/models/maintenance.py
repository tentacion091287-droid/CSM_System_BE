import enum
import uuid
from decimal import Decimal
from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base


class MaintenanceType(str, enum.Enum):
    routine = "routine"
    repair = "repair"
    inspection = "inspection"
    cleaning = "cleaning"


class MaintenanceStatus(str, enum.Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Maintenance(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False
    )
    maintenance_type: Mapped[MaintenanceType | None] = mapped_column(
        SAEnum(MaintenanceType, name="maintenancetype"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_date: Mapped[object] = mapped_column(Date, nullable=False)
    completed_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[MaintenanceStatus] = mapped_column(
        SAEnum(MaintenanceStatus, name="maintenancestatus"),
        nullable=False,
        server_default="scheduled",
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
