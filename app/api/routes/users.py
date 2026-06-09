from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Obtener todos los usuarios (solo si estás logueado)
@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    users = db.execute(select(User)).scalars().all()
    return users

# Obtener un usuario por ID
@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
