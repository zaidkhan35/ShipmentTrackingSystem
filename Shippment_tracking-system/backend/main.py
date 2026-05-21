from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine, SessionLocal
import models
from routers.auth_router  import router as auth_router
from routers.shipments    import router as shipments_router
from routers.other_routers import (
    tracking_router, users_router, products_router, dashboard_router
)
from auth import hash_password

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ShipTrack API",
    description="Shipment Tracking System — Group 20 | FastAPI + SQLite",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(shipments_router)
app.include_router(tracking_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(dashboard_router)

FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/", include_in_schema=False)
def serve():
    return FileResponse(os.path.join(FRONTEND, "index.html"))

if os.path.exists(FRONTEND):
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.on_event("startup")
def seed():
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            return

        # ── Admin ─────────────────────────────────────────────────────────────
        admin_user = models.User(email="admin@shiptrack.com",
                                  password=hash_password("admin123"), role="admin")
        db.add(admin_user); db.flush()
        admin = models.Admin(user_id=admin_user.user_id, full_name="System Admin")
        db.add(admin); db.flush()

        # ── Staff (Admin Supervises them) ──────────────────────────────────────
        staff_records = []
        for name, phone in [("Ali Raza", "0300-1111111"), ("Sara Khan", "0312-2222222")]:
            su = models.User(email=f"{name.split()[0].lower()}@shiptrack.com",
                              password=hash_password("staff123"), role="staff")
            db.add(su); db.flush()
            st = models.LogisticsStaff(user_id=su.user_id,
                                        supervised_by=admin.admin_id,   # Supervises
                                        full_name=name, phone_number=phone)
            db.add(st); db.flush()
            staff_records.append(st)

        # ── Customers (Admin Registers them) ───────────────────────────────────
        customer_data = [
            ("Muhammad Zaid",  "0321-1234567", "Peshawar, KPK",      "zaid@example.com"),
            ("Abdul Rehman",   "0333-2345678", "Lahore, Punjab",     "rehman@example.com"),
            ("Muhammad Bilal", "0345-3456789", "Karachi, Sindh",     "bilal@example.com"),
            ("Ayesha Malik",   "0301-4567890", "Islamabad, ICT",     "ayesha@example.com"),
        ]
        cust_records = []
        for name, phone, addr, email in customer_data:
            cu = models.User(email=email, password=hash_password("customer123"), role="customer")
            db.add(cu); db.flush()
            c = models.Customer(user_id=cu.user_id,
                                 registered_by=admin.admin_id,   # Registers
                                 full_name=name, phone_number=phone, address=addr)
            db.add(c); db.flush()
            cust_records.append(c)

        # ── Shipments (Staff Manages them) with MULTIPLE products each ─────────
        shipment_data = [
            (cust_records[0], staff_records[0], "Karachi",   "Lahore",     "in_transit", "2026-05-20",
             [("Laptop",      850.00), ("Mouse",    25.00), ("Keyboard", 45.00)]),
            (cust_records[1], staff_records[0], "Lahore",    "Peshawar",   "delivered",  "2026-05-10",
             [("Smartphone",  600.00), ("Charger",   15.00)]),
            (cust_records[2], staff_records[1], "Islamabad", "Quetta",     "pending",    "2026-05-25",
             [("Books",        30.00), ("Stationery", 10.00), ("Bag", 55.00)]),
            (cust_records[3], staff_records[1], "Multan",    "Faisalabad", "cancelled",  "2026-05-15",
             [("Clothes",      80.00)]),
            (cust_records[0], staff_records[0], "Peshawar",  "Karachi",    "in_transit", "2026-05-22",
             [("Camera",      400.00), ("Tripod",   60.00), ("Lens", 200.00), ("SD Card", 20.00)]),
            (cust_records[1], staff_records[1], "Quetta",    "Islamabad",  "delivered",  "2026-05-08",
             [("Shoes",        90.00), ("Socks",     8.00)]),
        ]

        tracking_templates = {
            "pending":    [("Origin Warehouse", "Shipment registered")],
            "in_transit": [("Origin Warehouse", "Shipment picked up"),
                           ("Sorting Hub",      "In transit at hub")],
            "delivered":  [("Origin Warehouse", "Shipment picked up"),
                           ("Sorting Hub",      "In transit at hub"),
                           ("Destination",      "Delivered to recipient")],
            "cancelled":  [("Origin Warehouse", "Shipment cancelled before dispatch")],
        }

        timestamps = ["2026-05-01T08:00:00", "2026-05-03T14:30:00", "2026-05-06T10:15:00"]

        for cust, staff, src, dest, status, eta, products in shipment_data:
            s = models.Shipment(customer_id=cust.customer_id, staff_id=staff.staff_id,
                                 source=src, destination=dest,
                                 delivery_status=status, estimated_delivery=eta)
            db.add(s); db.flush()

            # 1-to-MANY products per shipment
            for title, value in products:
                db.add(models.Product(shipment_id=s.shipment_id,
                                       title=title, value_usd=value))

            # Tracking history
            for i, (loc, msg) in enumerate(tracking_templates[status]):
                db.add(models.TrackingInfo(shipment_id=s.shipment_id,
                                            location=loc, status_update=msg,
                                            timestamp=timestamps[i]))

        db.commit()
        print("✅ Seed complete — admin@shiptrack.com / admin123")
        print("   Staff: ali@shiptrack.com / staff123")
        print("   Customer: zaid@example.com / customer123")
    finally:
        db.close()
