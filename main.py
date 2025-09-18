# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# --- DB core (lo que ya tenés en db/database.py) ---
from db.database import Base, engine, get_db

# --- Modelo ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ¡IMPORTANTE! crear las tablas **después** de definir el modelo
Base.metadata.create_all(bind=engine)

# --- Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    class Config:
        from_attributes = True  # pydantic v2

# --- Seguridad ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- App y endpoints ---
app = FastAPI(title="API del Sistema Académico")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del Sistema Académico"}

@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    user = User(
        email=payload.email,
        password_hash=pwd_context.hash(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()
