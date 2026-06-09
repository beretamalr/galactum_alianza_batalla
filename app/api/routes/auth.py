# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.schemas.token import TokenResponse
from app.models.user import User
from app.services import auth as auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        # Centralizamos toda la lógica de registro en el servicio
        new_user = auth_service.register_user(db, payload)
        
        # Crear el token de acceso para el nuevo usuario
        token = auth_service.create_access_token({"sub": new_user.email})
        
    except Exception as e:
        # Si el servicio lanza una excepción (ej: email duplicado), la capturamos
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return TokenResponse(
        status="success",
        message="User registered successfully.",
        token=token
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    # La lógica de autenticación se mueve al servicio
    user = auth_service.authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = auth_service.create_access_token({"sub": user.email})

    return TokenResponse(
        status="success",
        message="Login successful.",
        token=token
    )


@router.get("/me", response_model=UserOut, name="Me")
def me(current_user: User = Depends(auth_service.get_current_user)):
    """
    Obtiene la información del usuario actualmente autenticado.
    """
    return current_user

@router.get("/verify", name="Verify token")
def verify_token(current_user: User = Depends(auth_service.get_current_user)):
    return {"message": "Token válido", "user_email": current_user.email, "player_nickname": current_user.jugador.nickname if current_user.jugador else None}
