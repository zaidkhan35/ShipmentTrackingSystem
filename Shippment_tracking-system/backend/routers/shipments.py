from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/shipments", tags=["Shipments"])


@router.get("/", response_model=List[schemas.ShipmentOut])
def list_shipments(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Admin  → can view all shipments (read-only per ERD)
    Staff  → can view all shipments
    Customer → can only view their own shipments (Tracks relationship)
    """
    q = db.query(models.Shipment)

    if current_user.role == "customer":
        cust = db.query(models.Customer).filter(
            models.Customer.user_id == current_user.user_id).first()
        if not cust:
            return []
        q = q.filter(models.Shipment.customer_id == cust.customer_id)

    if status:
        q = q.filter(models.Shipment.delivery_status == status)

    return q.order_by(models.Shipment.shipment_id.desc()).all()


@router.get("/{shipment_id}", response_model=schemas.ShipmentOut)
def get_shipment(shipment_id: int, db: Session = Depends(get_db),
                 _=Depends(get_current_user)):
    s = db.query(models.Shipment).filter(
        models.Shipment.shipment_id == shipment_id).first()
    if not s:
        raise HTTPException(404, "Shipment not found")
    return s


# ── Q1 FIX: Only STAFF manages shipments (not Admin) ─────────────────────────

@router.post("/", response_model=schemas.ShipmentOut, status_code=201)
def create_shipment(
    payload: schemas.ShipmentCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("staff"))   # Staff only — Admin excluded
):
    s = models.Shipment(
        customer_id=payload.customer_id,
        staff_id=payload.staff_id,
        source=payload.source,
        destination=payload.destination,
        delivery_status=payload.delivery_status,
        estimated_delivery=payload.estimated_delivery
    )
    db.add(s); db.flush()

    # Q2 FIX: 1-to-Many — add ALL products from the list
    for p in (payload.products or []):
        db.add(models.Product(
            shipment_id=s.shipment_id,
            title=p.title,
            value_usd=p.value_usd
        ))

    db.commit(); db.refresh(s)
    return s


@router.patch("/{shipment_id}", response_model=schemas.ShipmentOut)
def update_shipment(
    shipment_id: int, payload: schemas.ShipmentUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role("staff"))   # Staff only — Admin excluded
):
    s = db.query(models.Shipment).filter(
        models.Shipment.shipment_id == shipment_id).first()
    if not s:
        raise HTTPException(404, "Shipment not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s


@router.delete("/{shipment_id}", status_code=204)
def delete_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("staff"))   # Q3 FIX: Staff CAN delete (they Manage shipments)
):
    s = db.query(models.Shipment).filter(
        models.Shipment.shipment_id == shipment_id).first()
    if not s:
        raise HTTPException(404, "Shipment not found")
    db.delete(s); db.commit()
