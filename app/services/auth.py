# app/services/auth.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.dependencies import get_db 
from app.schemas.user import UserCreate

# IMPORTACIONES DIRECTAS DE ARCHIVO
from app.services import ship_rooms_service
from app.services import inventory_service

# 🌟 CORRECCIÓN DEFINITIVA: Importando desde app.models.user (tu archivo real)
from app.models.user import User
from app.models.jugador import Jugador

settings = get_settings()

# Configuración del hash de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticación tipo "Bearer <token>"
bearer_scheme = HTTPBearer() 


def hash_password(password: str) -> str:
    """Genera el hash seguro de la contraseña."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica si la contraseña coincide con el hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, minutes: int | None = None) -> str:
    """Genera un token JWT con tiempo de expiración."""
    to_encode = data.copy()
    if minutes:
        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def register_user(db: Session, payload: UserCreate) -> User:
    """
    Maneja la lógica transaccional para registrar un nuevo usuario,
    su entidad Jugador, sus salas iniciales de la nave y su inventario base.
    """
    # 1. Verificar si el email o username ya existen para lanzar error temprano
    existing_user = db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first()
    if existing_user:
        raise Exception("El email o el nombre de usuario ya se encuentran registrados.")

    password_hash = hash_password(payload.password)
    
    try:
        # 2. CREAR USUARIO (USER)
        new_user = User(
            email=payload.email,
            username=payload.username,
            password_hash=password_hash
        )
        db.add(new_user)
        db.flush()  # Genera de forma segura el UUID en new_user.id
    
        # 3. CREAR JUGADOR (PLAYER)
        new_player = Jugador(
            user_id=new_user.id,
            nickname=payload.username
        )
        db.add(new_player)
        
        # VÍNCULO EXPLÍCITO EN MEMORIA: 
        new_user.jugador = new_player
        db.flush()  # Genera el ID numérico del jugador
    
        # 4. ORQUESTACIÓN DE SUB-SERVICIOS INICIALES
        ship_rooms_service.crear_salas_iniciales(db, user_id=new_user.id)
        inventory_service.crear_inventario_inicial(db, player_id=int(new_player.id))
        
        # 5. CONFIRMAR TODO EN LA BASE DE DATOS (COMMIT)
        db.commit()
        db.refresh(new_user)
        
        return new_user

    except Exception as e:
        # En caso de cualquier error intermedio, revertimos la transacción por completo
        db.rollback()
        raise e


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Valida las credenciales de un usuario para el inicio de sesión."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    """
    Dependencia global de FastAPI para endpoints protegidos.
    Extrae, decodifica el token Bearer JWT y retorna al usuario autenticado.
    """
    token = credentials.credentials

    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        sub: str | None = payload.get("sub")
        if sub is None:
            raise cred_exc
    except JWTError:
        raise cred_exc
        
    user = db.query(User).filter(User.email == sub).first()
    if user is None:
        raise cred_exc
        
    return user