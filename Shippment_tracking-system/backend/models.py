from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "User"
    user_id  = Column(Integer, primary_key=True, autoincrement=True)
    email    = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role     = Column(String(20),  nullable=False)   # admin | customer | staff

    admin    = relationship("Admin",          back_populates="user", uselist=False, cascade="all, delete")
    customer = relationship("Customer",       back_populates="user", uselist=False, cascade="all, delete")
    staff    = relationship("LogisticsStaff", back_populates="user", uselist=False, cascade="all, delete")


class Admin(Base):
    """
    ERD: Admin  --[Registers]-->  Customer
         Admin  --[Supervises]--> Logistics_Staff
    Admin does NOT manage shipments.
    """
    __tablename__ = "Admin"
    admin_id  = Column(Integer, primary_key=True, autoincrement=True)
    user_id   = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(100))

    user = relationship("User", back_populates="admin")

    # Tracks which customers this admin registered
    registered_customers = relationship("Customer", back_populates="registered_by_admin",
                                         foreign_keys="Customer.registered_by")
    # Tracks which staff this admin supervises
    supervised_staff = relationship("LogisticsStaff", back_populates="supervised_by_admin",
                                     foreign_keys="LogisticsStaff.supervised_by")


class Customer(Base):
    """ERD: Customer --[Tracks]--> Shipment (via customer_id FK on Shipment)"""
    __tablename__ = "Customer"
    customer_id   = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    registered_by = Column(Integer, ForeignKey("Admin.admin_id"), nullable=True)   # Registers relationship
    full_name     = Column(String(100))
    address       = Column(String(200))
    phone_number  = Column(String(20))

    user                 = relationship("User",  back_populates="customer",
                                         uselist=False, cascade="all, delete-orphan",
                                         single_parent=True)
    registered_by_admin  = relationship("Admin", back_populates="registered_customers",
                                         foreign_keys=[registered_by])
    shipments            = relationship("Shipment", back_populates="customer",
                                         cascade="all, delete-orphan")


class LogisticsStaff(Base):
    """ERD: Logistics_Staff --[Manages]--> Shipment (via staff_id FK on Shipment)"""
    __tablename__ = "Logistics_Staff"
    staff_id     = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    supervised_by = Column(Integer, ForeignKey("Admin.admin_id"), nullable=True)  # Supervises relationship
    full_name    = Column(String(100))
    phone_number = Column(String(20))

    user                = relationship("User",  back_populates="staff")
    supervised_by_admin = relationship("Admin", back_populates="supervised_staff",
                                        foreign_keys=[supervised_by])
    shipments           = relationship("Shipment", back_populates="staff")


class Shipment(Base):
    """
    ERD: Shipment --[Contains]--> Product  (1 to MANY)
         Shipment --[Has]-------> Tracking_Info (1 to MANY)
    """
    __tablename__ = "Shipment"
    shipment_id        = Column(Integer, primary_key=True, autoincrement=True)
    customer_id        = Column(Integer, ForeignKey("Customer.customer_id", ondelete="CASCADE"), nullable=False)
    staff_id           = Column(Integer, ForeignKey("Logistics_Staff.staff_id"), nullable=True)
    source             = Column(String(100))
    destination        = Column(String(100))
    delivery_status    = Column(String(20), nullable=False, default="pending")
    estimated_delivery = Column(String(20))

    customer      = relationship("Customer",       back_populates="shipments")
    staff         = relationship("LogisticsStaff", back_populates="shipments")
    # 1-to-MANY: one shipment contains many products
    products      = relationship("Product",      back_populates="shipment",
                                  cascade="all, delete-orphan")
    # 1-to-MANY: one shipment has many tracking updates
    tracking_info = relationship("TrackingInfo", back_populates="shipment",
                                  cascade="all, delete-orphan",
                                  order_by="TrackingInfo.timestamp.desc()")


class Product(Base):
    """
    ERD: Shipment 1 --[Contains]--> * Product
    A single shipment can contain MANY products.
    """
    __tablename__ = "Product"
    product_id  = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("Shipment.shipment_id", ondelete="CASCADE"), nullable=False)
    title       = Column(String(100))
    value_usd   = Column(Numeric(10, 2))

    shipment = relationship("Shipment", back_populates="products")


class TrackingInfo(Base):
    """ERD: Shipment 1 --[Has]--> * Tracking_Info"""
    __tablename__ = "Tracking_Info"
    tracking_id   = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id   = Column(Integer, ForeignKey("Shipment.shipment_id", ondelete="CASCADE"), nullable=False)
    location      = Column(String(100))
    status_update = Column(String(100))
    timestamp     = Column(String(30))

    shipment = relationship("Shipment", back_populates="tracking_info")
