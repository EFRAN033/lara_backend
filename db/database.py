# db/database.py

import os
from dotenv import load_dotenv
# ✨ 1. Importaciones adicionales necesarias
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ===================================================
# ✨ 2. MODELO 'User' CORREGIDO Y ACTUALIZADO ✨
# ===================================================
class User(Base):
    __tablename__ = "users"

    # Coincide con el 'uuid' de tu base de datos
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Columnas que faltaban en tu modelo original
    role_id = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ===================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()