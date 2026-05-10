from decimal import Decimal
from pydantic import BaseModel


class BookingStats(BaseModel):
    total: int
    pending: int
    approved: int
    active: int
    completed: int
    cancelled: int
    rejected: int


class VehicleStats(BaseModel):
    total: int
    available: int
    booked: int
    maintenance: int


class DriverStats(BaseModel):
    total: int
    available: int


class RevenueStats(BaseModel):
    total: Decimal
    this_month: Decimal


class PaymentStats(BaseModel):
    pending: int
    completed: int
    refunded: int


class FineStats(BaseModel):
    pending_count: int
    pending_amount: Decimal


class MaintenanceStats(BaseModel):
    scheduled: int
    in_progress: int


class MonthlyRevenue(BaseModel):
    month: str  # YYYY-MM
    revenue: Decimal


class DashboardResponse(BaseModel):
    bookings: BookingStats
    vehicles: VehicleStats
    drivers: DriverStats
    revenue: RevenueStats
    payments: PaymentStats
    fines: FineStats
    maintenance: MaintenanceStats
    monthly_revenue: list[MonthlyRevenue]
