# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada en las variables de entorno")
engine = create_engine(settings.DATABASE_URL) # type: ignore
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # type: ignore

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()