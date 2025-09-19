# db/database.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", back_populates="role")

# ✨ MODELO 'User' ACTUALIZADO CON TODOS LOS CAMPOS ✨
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    # --- ✨ NUEVOS CAMPOS AÑADIDOS ---
    dni = Column(String(20), unique=True, nullable=True) # DNI debe ser único
    phone = Column(String(20), nullable=True) # Teléfono puede ser opcional
    username = Column(String(100), unique=True, nullable=True) # Usuario debe ser único
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    role = relationship("Role", back_populates="users")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()