from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
import auth as au

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db),
             current_user: models.User = Depends(au.get_current_user)):
    """
    Only admins can register new users (ERD: Admin --[Registers]--> Customer).
    The admin_id is automatically recorded on Customer and LogisticsStaff.
    """
    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can register users")

    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    # Find the calling admin's profile
    admin_profile = db.query(models.Admin).filter(
        models.Admin.user_id == current_user.user_id).first()

    user = models.User(
        email=payload.email,
        password=au.hash_password(payload.password),
        role=payload.role
    )
    db.add(user); db.flush()

    if payload.role == "admin":
        db.add(models.Admin(user_id=user.user_id, full_name=payload.full_name))

    elif payload.role == "customer":
        # ERD: Admin Registers Customer — store which admin registered this customer
        db.add(models.Customer(
            user_id=user.user_id,
            registered_by=admin_profile.admin_id if admin_profile else None,
            full_name=payload.full_name,
            address=payload.address,
            phone_number=payload.phone_number
        ))

    elif payload.role == "staff":
        # ERD: Admin Supervises LogisticsStaff — store which admin supervises this staff
        db.add(models.LogisticsStaff(
            user_id=user.user_id,
            supervised_by=admin_profile.admin_id if admin_profile else None,
            full_name=payload.full_name,
            phone_number=payload.phone_number
        ))

    db.commit(); db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not au.verify_password(payload.password, user.password):
        raise HTTPException(401, "Invalid email or password")
    token = au.create_access_token({"sub": str(user.user_id), "role": user.role})
    return {"access_token": token, "token_type": "bearer",
            "role": user.role, "user_id": user.user_id}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user=Depends(au.get_current_user)):
    return current_user
