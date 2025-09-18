# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID # ✨ Importa UUID para Pydantic

# Importamos 'User' del archivo de base de datos
from db.database import get_db, User

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Modelos Pydantic ---
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserRead(BaseModel):
    id: UUID # ✨ El ID ahora es de tipo UUID
    email: str
    full_name: str
    role_id: int
    is_active: bool

    # ✨ Config actualizada para Pydantic v2
    model_config = ConfigDict(from_attributes=True)


# --- Endpoints ---
@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    
    user = User(
        email=payload.email,
        password_hash=pwd_context.hash(payload.password),
        full_name=payload.full_name,
        role_id=1,  # ✨ Asignamos un rol por defecto (ej. rol de estudiante)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@app.get("/users", response_model=list[UserRead])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()