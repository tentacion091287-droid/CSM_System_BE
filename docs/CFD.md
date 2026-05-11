# Context Flow Diagrams (CFD)

## Car Rental & Service Management System

This document describes the complete request/response flow for both the **User (Customer)** module and the **Admin** module.

---

## Part 1 — User (Customer) Module

### 1.1 Registration & Login

```
Customer                   API (FastAPI)              Database
   │                            │                         │
   ├─ POST /auth/register ──────►│                         │
   │  { email, password,        │ validate schema          │
   │    full_name }             │ check email unique ──────►│
   │                            │◄──────────────────────── │
   │                            │ hash password (bcrypt)   │
   │                            │ INSERT users ────────────►│
   │◄── 201 UserOut ────────────┤◄──────────────────────── │
   │                            │                         │
   ├─ POST /auth/login ─────────►│                         │
   │  { email, password }       │ SELECT user by email ───►│
   │                            │◄──────────────────────── │
   │                            │ verify password          │
   │                            │ sign JWT (HS256)         │
   │◄── 200 { access_token } ───┤                         │
```

---

### 1.2 View & Browse Vehicles

```
Customer                   API                        Database
   │                         │                            │
   ├─ GET /vehicles/ ────────►│                           │
   │  ?category=suv           │ SELECT vehicles           │
   │  ?date_from=2025-06-01   │ WHERE is_deleted=FALSE    │
   │  ?date_to=2025-06-05     │ AND NOT booked in range ─►│
   │  ?page=1&size=20         │                           │
   │                         │◄────────────────────────── │
   │◄── 200 [VehicleOut, ...] ┤ paginate results          │
   │                         │                            │
   ├─ GET /vehicles/{id} ────►│ SELECT vehicle by id ─────►│
   │                         │◄────────────────────────── │
   │◄── 200 VehicleOut ──────┤                            │
```

---

### 1.3 Create a Booking

```
Customer                   API                        Database
   │                         │                            │
   ├─ POST /bookings/ ───────►│                           │
   │  Authorization: Bearer   │ decode JWT → customer     │
   │  {                       │ validate dates            │
   │    vehicle_id,           │ check vehicle available ─►│
   │    pickup_date,          │                           │
   │    return_date,          │◄────────────────────────── │
   │    needs_driver,         │ calculate estimated_cost  │
   │    pickup_location,      │   = days × daily_rate     │
   │    drop_location         │ INSERT booking ───────────►│
   │  }                       │   status = "pending"       │
   │                         │◄────────────────────────── │
   │◄── 201 BookingOut ──────┤                            │
   │    status: pending       │                           │
```

---

### 1.4 Booking Approval & Activation (Customer View)

```
Customer                   API                     Admin          Database
   │                         │                       │               │
   │  [booking is pending]   │                       │               │
   │                         │◄─ PATCH /approve ─────┤               │
   │                         │  update status ────────────────────►  │
   │                         │  = "approved"          │               │
   │                         │◄────────────────────────────────────── │
   │                         │                       │               │
   │  GET /bookings/{id} ───►│  SELECT booking ──────────────────────►│
   │◄── 200 status:approved  │◄────────────────────────────────────── │
   │                         │                       │               │
   │  [admin activates on    │◄─ PATCH /activate ────┤               │
   │   pickup day]           │  update status ────────────────────►  │
   │                         │  = "active"            │               │
   │                         │  update vehicle ───────────────────►  │
   │                         │  status = "booked"     │               │
   │◄── status: active ──────┤                       │               │
```

---

### 1.5 Make a Payment

```
Customer                   API                        Database
   │                         │                            │
   ├─ POST /payments/ ───────►│                           │
   │  {                       │ decode JWT                │
   │    booking_id,           │ verify booking belongs    │
   │    payment_method: "upi" │ to this customer ─────────►│
   │  }                       │◄────────────────────────── │
   │                         │ INSERT payment ───────────►│
   │                         │   status = "pending"       │
   │◄── 201 PaymentOut ──────┤◄────────────────────────── │
   │    status: pending       │                           │
   │                         │                           │
   │  [admin processes]       │                           │
   │                         │◄─ PATCH /process ──────── (Admin)
   │                         │  UPDATE payment status ───►│
   │                         │  = "completed"             │
   │                         │  auto-INSERT invoice ──────►│
   │                         │    base + fine + tax       │
   │                         │◄────────────────────────── │
```

---

### 1.6 View Invoice

```
Customer                   API                        Database
   │                         │                            │
   ├─ GET /invoices/my ──────►│                           │
   │  Authorization: Bearer   │ decode JWT → customer_id  │
   │                         │ SELECT invoices            │
   │                         │ JOIN bookings              │
   │                         │ WHERE customer_id = ? ────►│
   │◄── 200 [InvoiceOut, ...] ┤◄────────────────────────── │
   │                         │                            │
   ├─ GET /invoices/{id} ────►│ SELECT invoice by id ─────►│
   │                         │ verify customer owns it    │
   │◄── 200 InvoiceOut ──────┤◄────────────────────────── │
```

---

### 1.7 View & Pay Fine

```
Customer                   API                        Database
   │                         │                            │
   ├─ GET /fines/my ─────────►│                           │
   │                         │ SELECT fines               │
   │                         │ WHERE customer_id = ? ────►│
   │◄── 200 [FineOut, ...] ──┤◄────────────────────────── │
   │    status: pending       │                           │
   │                         │                           │
   ├─ PATCH /fines/{id}/pay ─►│                           │
   │                         │ UPDATE fine status ────────►│
   │                         │ = "paid"                   │
   │                         │ SET paid_at = now()        │
   │◄── 200 FineOut ─────────┤◄────────────────────────── │
   │    status: paid          │                           │
```

---

### 1.8 Rate a Driver

```
Customer                   API                        Database
   │                         │                            │
   ├─ POST /drivers/ratings ─►│                           │
   │  {                       │ verify booking belongs    │
   │    driver_id,            │ to this customer ─────────►│
   │    booking_id,           │ verify booking completed  │
   │    rating: 5,            │ verify driver was assigned│
   │    review: "Great!"      │ INSERT driver_rating ─────►│
   │  }                       │ UPDATE driver.avg_rating  │
   │                         │ recalculate from all ──────►│
   │                         │◄────────────────────────── │
   │◄── 201 RatingOut ───────┤                            │
```

---

### 1.9 Manage Profile

```
Customer                   API                        Database
   │                         │                            │
   ├─ GET /auth/me ──────────►│                           │
   │  Authorization: Bearer   │ decode JWT → user_id      │
   │                         │ SELECT user by id ─────────►│
   │◄── 200 UserOut ─────────┤◄────────────────────────── │
   │                         │                            │
   ├─ PUT /auth/me ──────────►│                           │
   │  { full_name, phone }    │ UPDATE users ─────────────►│
   │◄── 200 UserOut ─────────┤◄────────────────────────── │
   │                         │                            │
   ├─ PUT /auth/me/password ─►│                           │
   │  { old_password,         │ verify old password       │
   │    new_password }        │ hash new password         │
   │                         │ UPDATE hashed_password ───►│
   │◄── 204 ─────────────────┤◄────────────────────────── │
```

---

## Part 2 — Admin Module

### 2.1 Admin Login

```
Admin                      API                        Database
  │                          │                            │
  ├─ POST /auth/login ───────►│                           │
  │  { email, password }     │ SELECT user by email ─────►│
  │                          │◄────────────────────────── │
  │                          │ verify password            │
  │                          │ verify role == "admin"     │
  │                          │ sign JWT with role: admin  │
  │◄── 200 { access_token }  ┤                           │
```

---

### 2.2 Dashboard Statistics

```
Admin                      API                        Database
  │                          │                            │
  ├─ GET /admin/dashboard ───►│                           │
  │  Authorization: Bearer   │ require_admin dependency  │
  │                          │ parallel queries:         │
  │                          │  SELECT COUNT(users) ─────►│
  │                          │  SELECT COUNT(vehicles) ──►│
  │                          │  SELECT COUNT(bookings) ──►│
  │                          │  SELECT SUM(payments) ────►│
  │                          │  SELECT COUNT(active) ────►│
  │                          │◄────────────────────────── │
  │◄── 200 DashboardStats ───┤ aggregate stats           │
  │  {                        │                          │
  │    total_users,           │                          │
  │    total_vehicles,        │                          │
  │    active_bookings,       │                          │
  │    total_revenue,         │                          │
  │    pending_bookings       │                          │
  │  }                        │                          │
```

---

### 2.3 User Management

```
Admin                      API                        Database
  │                          │                            │
  ├─ GET /admin/users ───────►│                           │
  │  ?page=1&size=20          │ SELECT users              │
  │                          │ WHERE is_deleted=FALSE ───►│
  │◄── 200 Page[UserOut] ────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /users/{id}/       │                           │
  │    activate ─────────────►│ SELECT user ──────────────►│
  │                          │ toggle is_active ──────────►│
  │◄── 200 UserOut ──────────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /users/{id}/       │                           │
  │    role ─────────────────►│ { role: "admin" }         │
  │                          │ UPDATE users.role ─────────►│
  │◄── 200 UserOut ──────────┤◄────────────────────────── │
```

---

### 2.4 Vehicle Fleet Management

```
Admin                      API                        Database
  │                          │                            │
  ├─ POST /vehicles/ ────────►│                           │
  │  { make, model, year,    │ validate schema            │
  │    license_plate,        │ check plate unique ────────►│
  │    category, daily_rate  │◄────────────────────────── │
  │    fuel_type, seats }    │ INSERT vehicle ───────────►│
  │◄── 201 VehicleOut ───────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /vehicles/{id}/   │                           │
  │    status ───────────────►│ { status: "maintenance" } │
  │                          │ UPDATE vehicle.status ────►│
  │◄── 200 VehicleOut ───────┤◄────────────────────────── │
  │                          │                            │
  ├─ DELETE /vehicles/{id} ──►│ soft delete               │
  │                          │ UPDATE is_deleted=TRUE ───►│
  │◄── 204 ──────────────────┤◄────────────────────────── │
```

---

### 2.5 Booking Lifecycle Management

```
Admin                      API                        Database
  │                          │                            │
  │  [new booking arrives]   │                           │
  │                          │                           │
  ├─ GET /bookings/ ─────────►│                          │
  │  [see all pending]       │ SELECT bookings ───────────►│
  │◄── 200 Page[BookingOut] ─┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/approve ────►│                          │
  │  { admin_notes }         │ UPDATE status="approved" ─►│
  │◄── 200 BookingOut ───────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/assign-     │                           │
  │    driver ───────────────►│ { driver_id }            │
  │                          │ UPDATE booking.driver_id ─►│
  │◄── 200 BookingOut ───────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/activate ───►│ [on pickup day]          │
  │                          │ UPDATE status="active" ───►│
  │                          │ UPDATE vehicle            │
  │                          │   status="booked" ─────────►│
  │◄── 200 BookingOut ───────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/complete ───►│ [on return]              │
  │                          │ UPDATE status="completed"  │
  │                          │ UPDATE vehicle            │
  │                          │   status="available" ──────►│
  │                          │ check actual_return        │
  │                          │ > return_date?             │
  │                          │   YES → INSERT fine ───────►│
  │◄── 200 BookingOut ───────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/reject ─────►│                          │
  │  { admin_notes }         │ UPDATE status="rejected" ─►│
  │◄── 200 BookingOut ───────┤◄────────────────────────── │
```

---

### 2.6 Payment Processing & Refunds

```
Admin                      API                        Database
  │                          │                            │
  ├─ GET /payments/ ─────────►│                          │
  │  [see all payments]       │ SELECT payments ───────────►│
  │◄── 200 Page[PaymentOut] ─┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/process ────►│                          │
  │                          │ UPDATE payment            │
  │                          │   status="completed"       │
  │                          │   paid_at=now() ───────────►│
  │                          │ auto-create Invoice        │
  │                          │   base + fine + tax ───────►│
  │◄── 200 PaymentOut ───────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/refund ─────►│                          │
  │                          │ UPDATE payment            │
  │                          │   status="refunded" ───────►│
  │◄── 200 PaymentOut ───────┤◄────────────────────────── │
```

---

### 2.7 Fine Management

```
Admin                      API                        Database
  │                          │                            │
  ├─ GET /fines/ ────────────►│                          │
  │  [all fines]             │ SELECT fines ─────────────►│
  │◄── 200 Page[FineOut] ────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /fines/{id}/waive ►│                          │
  │                          │ UPDATE fine.status        │
  │                          │   = "waived" ──────────────►│
  │◄── 200 FineOut ──────────┤◄────────────────────────── │
```

---

### 2.8 Driver Management

```
Admin                      API                        Database
  │                          │                            │
  ├─ POST /drivers/ ─────────►│                          │
  │  { full_name, phone,     │ validate schema            │
  │    license_number,       │ check phone unique ────────►│
  │    license_expiry }      │◄────────────────────────── │
  │                          │ INSERT driver ─────────────►│
  │◄── 201 DriverOut ────────┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/availability►│                          │
  │  { is_available: false } │ UPDATE driver             │
  │                          │   is_available = false ───►│
  │◄── 200 DriverOut ────────┤◄────────────────────────── │
  │                          │                            │
  ├─ GET /{id}/ratings ──────►│                          │
  │                          │ SELECT driver_ratings      │
  │                          │ WHERE driver_id = ? ───────►│
  │◄── 200 Page[RatingOut] ──┤◄────────────────────────── │
```

---

### 2.9 Vehicle Maintenance

```
Admin                      API                        Database
  │                          │                            │
  ├─ POST /maintenance/ ─────►│                          │
  │  { vehicle_id,           │ validate schema            │
  │    maintenance_type,     │ INSERT maintenance_record ─►│
  │    scheduled_date,       │   status="scheduled"       │
  │    description }         │                            │
  │◄── 201 MaintenanceOut ───┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/complete ───►│                          │
  │                          │ UPDATE status="completed" ─►│
  │                          │ SET completed_date=today   │
  │◄── 200 MaintenanceOut ───┤◄────────────────────────── │
  │                          │                            │
  ├─ PATCH /{id}/cancel ─────►│                          │
  │                          │ UPDATE status="cancelled" ─►│
  │◄── 200 MaintenanceOut ───┤◄────────────────────────── │
```

---

## Part 3 — Complete System Interaction Map

```
┌────────────────────────────────────────────────────────────────┐
│                          CUSTOMER                               │
│                                                                  │
│  Register/Login → Browse Vehicles → Create Booking              │
│       │                                     │                   │
│       │                          [Wait for admin approval]      │
│       │                                     │                   │
│       │                          [Booking: approved → active]   │
│       │                                     │                   │
│       └────────────────► Make Payment ───────►                  │
│                          View Invoice                           │
│                          Pay Fine (if overdue)                  │
│                          Rate Driver (if assigned)              │
└────────────────────────────────────────────────────────────────┘
                               ▲  ▼  (API calls)
┌────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                          │
│                                                                  │
│  JWT Auth ──► Role Check ──► Router ──► Service ──► ORM         │
└────────────────────────────────────────────────────────────────┘
                               ▲  ▼  (asyncpg / NullPool)
┌────────────────────────────────────────────────────────────────┐
│               SUPABASE (PostgreSQL + PgBouncer)                  │
│                                                                  │
│  users  vehicles  drivers  bookings  payments                   │
│  invoices  fines  maintenance_records  driver_ratings           │
└────────────────────────────────────────────────────────────────┘
                               ▲  ▼  (manage)
┌────────────────────────────────────────────────────────────────┐
│                           ADMIN                                  │
│                                                                  │
│  Dashboard → Manage Users → Manage Fleet → Review Bookings      │
│  Process Payments → Manage Fines → Schedule Maintenance         │
│  Manage Drivers → Assign Drivers to Bookings                    │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 4 — Authentication Flow Summary

```
Request with Bearer Token
         │
         ▼
HTTPBearer() extracts token from "Authorization: Bearer <token>" header
         │
         ▼
jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
         │
    ┌────┴────┐
  Valid?    Expired/Invalid?
    │             │
    ▼             ▼
SELECT user    401 Unauthorized
by sub (id)
    │
    ├─ User not found?  → 401
    ├─ is_active=False? → 401
    │
    ▼
User object injected into route handler
    │
Admin-only route?
    │
    ├─ role != admin → 403 Forbidden
    │
    ▼
Handler executes
```
