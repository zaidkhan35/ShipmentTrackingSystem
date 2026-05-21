from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database import get_db
import models, schemas
from auth import get_current_user, require_role

# ── Tracking ──────────────────────────────────────────────────────────────────
tracking_router = APIRouter(prefix="/api/tracking", tags=["Tracking"])

@tracking_router.get("/{shipment_id}", response_model=List[schemas.TrackingOut])
def get_tracking(shipment_id: int, db: Session = Depends(get_db),
                 _=Depends(get_current_user)):
    if not db.query(models.Shipment).filter(
            models.Shipment.shipment_id == shipment_id).first():
        raise HTTPException(404, "Shipment not found")
    return (db.query(models.TrackingInfo)
              .filter(models.TrackingInfo.shipment_id == shipment_id)
              .order_by(models.TrackingInfo.timestamp.desc())
              .all())

@tracking_router.post("/{shipment_id}", response_model=schemas.TrackingOut, status_code=201)
def add_tracking(shipment_id: int, payload: schemas.TrackingCreate,
                 db: Session = Depends(get_db),
                 _=Depends(require_role("staff"))):   # Staff only
    if not db.query(models.Shipment).filter(
            models.Shipment.shipment_id == shipment_id).first():
        raise HTTPException(404, "Shipment not found")
    entry = models.TrackingInfo(
        shipment_id=shipment_id,
        location=payload.location,
        status_update=payload.status_update,
        timestamp=payload.timestamp or datetime.utcnow().isoformat()
    )
    db.add(entry); db.commit(); db.refresh(entry)
    return entry

@tracking_router.delete("/{tracking_id}", status_code=204)
def delete_tracking(tracking_id: int, db: Session = Depends(get_db),
                    _=Depends(require_role("staff"))):  # Q3 FIX: Staff can delete
    e = db.query(models.TrackingInfo).filter(
        models.TrackingInfo.tracking_id == tracking_id).first()
    if not e:
        raise HTTPException(404, "Not found")
    db.delete(e); db.commit()


# ── Users ─────────────────────────────────────────────────────────────────────
users_router = APIRouter(prefix="/api/users", tags=["Users"])

@users_router.get("/customers", response_model=List[schemas.CustomerOut])
def list_customers(db: Session = Depends(get_db),
                   _=Depends(require_role("admin", "staff"))):
    return db.query(models.Customer).all()

@users_router.get("/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db),
                 _=Depends(require_role("admin", "staff"))):
    c = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id).first()
    if not c: raise HTTPException(404, "Customer not found")
    return c

@users_router.patch("/customers/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(customer_id: int, payload: schemas.CustomerUpdate,
                    db: Session = Depends(get_db),
                    _=Depends(require_role("admin"))):   # Admin updates customer info
    c = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id).first()
    if not c: raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    return c

@users_router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db),
                    _=Depends(require_role("admin"))):   # Admin can remove customers
    c = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id).first()
    if not c: raise HTTPException(404, "Not found")
    if c.user:
        db.delete(c.user)
    else:
        db.delete(c)
    db.commit()

@users_router.get("/staff", response_model=List[schemas.StaffOut])
def list_staff(db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    return db.query(models.LogisticsStaff).all()

@users_router.delete("/staff/{staff_id}", status_code=204)
def delete_staff(staff_id: int, db: Session = Depends(get_db),
                 _=Depends(require_role("admin"))):   # Q3 FIX: Admin can delete staff
    s = db.query(models.LogisticsStaff).filter(
        models.LogisticsStaff.staff_id == staff_id).first()
    if not s: raise HTTPException(404, "Not found")
    db.delete(s); db.commit()


# ── Products (1-to-Many) ──────────────────────────────────────────────────────
products_router = APIRouter(prefix="/api/products", tags=["Products"])

@products_router.get("/shipment/{shipment_id}", response_model=List[schemas.ProductOut])
def list_products(shipment_id: int, db: Session = Depends(get_db),
                  _=Depends(get_current_user)):
    """Returns ALL products for a shipment (1-to-Many)"""
    return (db.query(models.Product)
              .filter(models.Product.shipment_id == shipment_id)
              .all())

@products_router.post("/shipment/{shipment_id}", response_model=schemas.ProductOut, status_code=201)
def add_product(shipment_id: int, payload: schemas.ProductCreate,
                db: Session = Depends(get_db),
                _=Depends(require_role("staff"))):   # Staff manages products
    if not db.query(models.Shipment).filter(
            models.Shipment.shipment_id == shipment_id).first():
        raise HTTPException(404, "Shipment not found")
    p = models.Product(shipment_id=shipment_id,
                        title=payload.title, value_usd=payload.value_usd)
    db.add(p); db.commit(); db.refresh(p)
    return p

@products_router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db),
                   _=Depends(require_role("staff"))):   # Staff removes products
    p = db.query(models.Product).filter(
        models.Product.product_id == product_id).first()
    if not p: raise HTTPException(404, "Not found")
    db.delete(p); db.commit()


# ── Dashboard ──────────────────────────────────────────────────────────────────
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@dashboard_router.get("/stats", response_model=schemas.DashboardStats)
def stats(db: Session = Depends(get_db),
          _=Depends(require_role("admin", "staff"))):
    def cnt(s):
        return db.query(models.Shipment).filter(
            models.Shipment.delivery_status == s).count()
    return {
        "total_shipments":  db.query(models.Shipment).count(),
        "pending":          cnt("pending"),
        "in_transit":       cnt("in_transit"),
        "delivered":        cnt("delivered"),
        "cancelled":        cnt("cancelled"),
        "total_customers":  db.query(models.Customer).count(),
        "total_staff":      db.query(models.LogisticsStaff).count(),
    }
