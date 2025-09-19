# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from db.database import get_db, User, Role 

# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = "tu_super_secreto_aqui"  # ¡Es crucial cambiar esto en producción!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# --- MIDDLEWARE CORS ---
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- MODELOS PYDANTIC (Esquemas de Datos) ---

class UserBase(BaseModel):
    full_name: str
    dni: str
    email: str
    phone: str | None = None
    username: str

class UserCreate(UserBase):
    password: str
    role: str # 'student' o 'teacher'

class UserUpdate(BaseModel):
    full_name: str | None = None
    dni: str | None = None
    email: str | None = None
    phone: str | None = None
    username: str | None = None
    password: str | None = None
    role_id: int | None = None

class UserRead(UserBase):
    id: UUID
    role_id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

# --- FUNCIONES DE UTILIDAD ---

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- ENDPOINTS DE LA API ---

@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Validaciones para evitar duplicados
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="El correo electrónico ya está registrado")
    if db.query(User).filter(User.dni == payload.dni).first():
        raise HTTPException(status_code=409, detail="El DNI ya está registrado")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="El nombre de usuario ya está en uso")

    # Mapear el rol de texto a su ID correspondiente en la base de datos
    role_map = {"student": 2, "teacher": 3} # Asegúrate de que estos IDs existan en tu tabla 'roles'
    role_id = role_map.get(payload.role)
    if not role_id:
        raise HTTPException(status_code=400, detail="Rol inválido. Debe ser 'student' o 'teacher'.")

    # Crear el nuevo objeto de usuario con los datos del payload
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=pwd_context.hash(payload.password),
        dni=payload.dni,
        phone=payload.phone,
        username=payload.username,
        role_id=role_id,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@app.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.role)).filter(User.email == form_data.username).first()
    
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear el payload del token con la información necesaria para el frontend
    access_token_data = {
        "sub": user.email,
        "full_name": user.full_name,
        "role": user.role.name
    }
    
    access_token = create_access_token(data=access_token_data)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users", response_model=list[UserRead])
def get_users(db: Session = Depends(get_db)):
    """Obtiene una lista de todos los usuarios."""
    return db.query(User).all()

@app.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, payload: UserUpdate, db: Session = Depends(get_db)):
    """Actualiza la información de un usuario existente."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = payload.model_dump(exclude_unset=True)
    
    # Si se envía una nueva contraseña, se hashea.
    if "password" in update_data and update_data["password"]:
        user.password_hash = pwd_context.hash(update_data["password"])
        del update_data["password"]

    for key, value in update_data.items():
        setattr(user, key, value)
        
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    """Elimina un usuario de la base de datos."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    db.delete(user)
    db.commit()
    return