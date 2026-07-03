# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.schemas.user import UserCreate, UserLogin, Token
from app.services import auth as auth_service

# Apuntando a tu archivo real models/user.py
from app.models.user import User

# Esta variable DEBE llamarse 'router'
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, name="Register user")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario, crea su comandante (jugador),
    inicializa sus salas de la nave y su inventario base.
    """
    try:
        new_user = auth_service.register_user(db, payload)
        access_token = auth_service.create_access_token(data={"sub": new_user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token, name="Login user")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Inicia sesión verificando las credenciales y devuelve el token JWT.
    """
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify", name="Verify token")
def verify_token(current_user: User = Depends(auth_service.get_current_user)):
    """
    Endpoint que usa Godot para validar que el jugador está conectado
    y obtener los datos de su comandante en la pantalla principal.
    """
    return {
        "message": "Token válido", 
        "user_email": current_user.email, 
        "player_nickname": current_user.jugador.nickname if current_user.jugador else None
    }