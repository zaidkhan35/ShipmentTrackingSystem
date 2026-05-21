from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum


class RoleEnum(str, Enum):
    admin    = "admin"
    customer = "customer"
    staff    = "staff"


class DeliveryStatusEnum(str, Enum):
    pending    = "pending"
    in_transit = "in_transit"
    delivered  = "delivered"
    cancelled  = "cancelled"


# ── Auth ──────────────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type:   str
    role:         str
    user_id:      int

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


# ── User ──────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email:        EmailStr
    password:     str
    role:         RoleEnum
    full_name:    Optional[str] = None
    address:      Optional[str] = None
    phone_number: Optional[str] = None
    # Admin may pass these when registering/supervising
    admin_id:     Optional[int] = None

class UserOut(BaseModel):
    user_id: int
    email:   str
    role:    str
    class Config: from_attributes = True


# ── Customer ──────────────────────────────────────────────────────────────────
class CustomerOut(BaseModel):
    customer_id:   int
    user_id:       int
    registered_by: Optional[int]
    full_name:     Optional[str]
    address:       Optional[str]
    phone_number:  Optional[str]
    class Config: from_attributes = True

class CustomerUpdate(BaseModel):
    full_name:    Optional[str] = None
    address:      Optional[str] = None
    phone_number: Optional[str] = None


# ── Staff ─────────────────────────────────────────────────────────────────────
class StaffOut(BaseModel):
    staff_id:      int
    user_id:       int
    supervised_by: Optional[int]
    full_name:     Optional[str]
    phone_number:  Optional[str]
    class Config: from_attributes = True


# ── Product (1-to-Many with Shipment) ─────────────────────────────────────────
class ProductCreate(BaseModel):
    title:     Optional[str]   = None
    value_usd: Optional[float] = None

class ProductOut(BaseModel):
    product_id:  int
    shipment_id: int
    title:       Optional[str]
    value_usd:   Optional[float]
    class Config: from_attributes = True


# ── Tracking ──────────────────────────────────────────────────────────────────
class TrackingCreate(BaseModel):
    location:      Optional[str] = None
    status_update: Optional[str] = None
    timestamp:     Optional[str] = None

class TrackingOut(BaseModel):
    tracking_id:   int
    shipment_id:   int
    location:      Optional[str]
    status_update: Optional[str]
    timestamp:     Optional[str]
    class Config: from_attributes = True


# ── Shipment ──────────────────────────────────────────────────────────────────
class ShipmentCreate(BaseModel):
    customer_id:        int
    staff_id:           Optional[int]    = None
    source:             Optional[str]    = None
    destination:        Optional[str]    = None
    delivery_status:    DeliveryStatusEnum = DeliveryStatusEnum.pending
    estimated_delivery: Optional[str]    = None
    products:           Optional[List[ProductCreate]] = []   # 1-to-Many

class ShipmentUpdate(BaseModel):
    staff_id:           Optional[int]              = None
    source:             Optional[str]              = None
    destination:        Optional[str]              = None
    delivery_status:    Optional[DeliveryStatusEnum] = None
    estimated_delivery: Optional[str]              = None

class ShipmentOut(BaseModel):
    shipment_id:        int
    customer_id:        int
    staff_id:           Optional[int]
    source:             Optional[str]
    destination:        Optional[str]
    delivery_status:    str
    estimated_delivery: Optional[str]
    products:           List[ProductOut]   = []   # Many products
    tracking_info:      List[TrackingOut]  = []
    class Config: from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_shipments:  int
    pending:          int
    in_transit:       int
    delivered:        int
    cancelled:        int
    total_customers:  int
    total_staff:      int
