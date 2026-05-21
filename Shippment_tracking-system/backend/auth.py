from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models, os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _safe(pw: str) -> str:
    """Bcrypt hard limit is 72 bytes — truncate to avoid ValueError in bcrypt 4.x"""
    return pw.encode("utf-8")[:72].decode("utf-8", errors="ignore")

def hash_password(pw: str) -> str:
    return pwd_context.hash(_safe(pw))

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_safe(plain), hashed)

def create_access_token(data: dict) -> str:
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)):
    exc = HTTPException(status_code=401, detail="Invalid credentials",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid = payload.get("sub")
        if uid is None: raise exc
    except JWTError:
        raise exc
    user = db.query(models.User).filter(models.User.user_id == int(uid)).first()
    if not user: raise exc
    return user

def require_role(*roles):
    def checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current_user
    return checker
